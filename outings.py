"""Percival Outings: exact scheduled round trips with a minimum visit.

The selected-destination workflow uses forward-certified itineraries for both
legs. Candidate browsing is deliberately bounded; unevaluated destinations are
reported as incomplete search, never silently classified as unreachable.
"""
import routing


def _coverage_problem(stop_id, coverage_rows):
    feed = stop_id.split(':', 1)[0]
    row = next((item for item in coverage_rows if item.get('feed') == feed), None)
    if row is None:
        return dict(code='coverage_unknown', message=f'No coverage record is available for {feed}.')
    if row.get('status') != 'imported':
        return dict(code='feed_unavailable', message=f'{feed} is not imported for this search.')
    if not row.get('in_service_period', True):
        return dict(code='outside_service_period', message=f'{feed} is outside its loaded service period on this date.')
    return None


def _incomplete_coverage(coverage_rows):
    missing = [row['feed'] for row in coverage_rows
               if row.get('status') != 'imported'
               or not row.get('in_service_period', True)]
    if missing:
        return dict(code='incomplete_coverage',
                    message='Cannot rule out another journey while these feeds are unavailable or out of period: '
                            + ', '.join(sorted(missing)) + '.')
    return None


def _scheduled_plan(arrival, path, day, start, coverage_rows):
    legs = [dict(leg) for leg in path]
    return dict(
        found=True,
        departure=legs[0]['departure'] if legs else start,
        arrival=arrival,
        legs=legs,
        estimated_ground_meters=sum(leg.get('meters', 0) for leg in legs),
        coverage=coverage_rows,
        status='Scheduled feasibility only; transfers and ground links are estimates.',
    )


def _base(day, origin, destination, earliest, home_by, minimum_stay,
          outbound_budget, coverage_rows):
    stops = routing.network()[0]
    if origin not in stops:
        raise ValueError('Unknown origin stop')
    if destination not in stops:
        raise ValueError('Unknown destination stop')
    return dict(
        status='unknown', scheduled=True, date=day, origin=origin,
        destination=dict(id=destination, name=stops[destination]['name'],
                         lat=stops[destination]['lat'], lon=stops[destination]['lon']),
        earliest_departure=earliest, home_by=home_by,
        minimum_stay=minimum_stay, outbound_budget=outbound_budget,
        coverage=coverage_rows,
    )


def evaluate(day, origin, destination, earliest, home_by, minimum_stay=7200,
             outbound_budget=3600, mode='walk', radius=500, buffer=300,
             feeds=(), coverage_rows=None, outbound=None, latest_return=True):
    """Evaluate one destination with exact forward plans in both directions."""
    coverage_rows = coverage_rows or []
    result = _base(day, origin, destination, earliest, home_by, minimum_stay,
                   outbound_budget, coverage_rows)
    problems = [problem for stop in (origin, destination)
                if (problem := _coverage_problem(stop, coverage_rows))]
    if problems:
        result['reason'] = problems[0]
        return result

    opts = dict(mode=mode, radius=radius, buffer=buffer, feeds=feeds)
    outbound_deadline = min(home_by, earliest + outbound_budget)
    if outbound is None:
        outbound = routing.plan(day, origin, destination, earliest,
                                outbound_deadline, **opts)
    if not outbound.get('found'):
        problem = _incomplete_coverage(coverage_rows)
        result.update(status='unknown' if problem else 'ruled_out', reason=problem or dict(
            code='no_outbound_within_budget',
            message='No scheduled outbound itinerary reaches this stop within the outbound budget.'))
        return result

    result['outbound'] = outbound
    ready = outbound['arrival'] + minimum_stay
    if ready > home_by:
        problem = _incomplete_coverage(coverage_rows)
        result.update(status='unknown' if problem else 'ruled_out', reason=problem or dict(
            code='insufficient_time_together',
            message='The outbound arrival leaves less than the requested meeting time before home-by.'))
        return result

    earliest_return = routing.plan(day, destination, origin, ready, home_by,
                                   **opts)
    if not earliest_return.get('found'):
        any_return = routing.plan(day, destination, origin, outbound['arrival'],
                                  home_by, **opts)
        if any_return.get('found'):
            reason = dict(
                code='insufficient_time_together',
                message='A scheduled return exists, but it leaves before the minimum meeting time is complete.')
        else:
            reason = dict(
                code='no_usable_return',
                message='No scheduled return itinerary reaches home by the selected deadline.')
        problem = _incomplete_coverage(coverage_rows)
        result.update(status='unknown' if problem else 'ruled_out', reason=problem or reason)
        return result

    # routing.latest searches minute boundaries. Its floor-rounded first
    # minute can precede the exact end of the required stay; never accept it
    # without a second-level check. The earliest forward plan remains a safe
    # certified fallback for a return inside that boundary minute.
    minute_start = ((ready + 59) // 60) * 60
    return_trip = earliest_return
    if latest_return and minute_start <= home_by:
        candidate = routing.latest(day, destination, origin, minute_start,
                                   home_by, **opts)
        if candidate.get('found') and candidate['departure'] >= ready:
            return_trip = candidate
    if not return_trip.get('found'):
        result.update(status='unknown', reason=dict(
            code='incomplete_return_search',
            message='A return was found, but the latest-return search could not certify an itinerary.'))
        return result
    leave_destination = return_trip['departure']
    if leave_destination < ready or return_trip['arrival'] > home_by:
        result.update(status='unknown', reason=dict(
            code='return_certification_failed',
            message='The returned itinerary did not satisfy the exact stay and home-by limits.'))
        return result
    result.update(
        status='verified',
        reason=dict(code='scheduled_round_trip', message='Both legs are verified against the active scheduled data.'),
        return_trip=return_trip,
        meeting_window=dict(start=outbound['arrival'], end=leave_destination,
                            seconds=max(0, leave_destination - outbound['arrival'])),
        leave_origin=outbound['departure'],
        latest_verified_return_departure=leave_destination,
        home_arrival=return_trip['arrival'],
    )
    return result


def browse(day, origin, earliest, home_by, minimum_stay=7200,
           outbound_budget=3600, mode='walk', radius=500, buffer=300,
           feeds=(), coverage_rows=None, limit=40):
    """Forward-certify round trips for a bounded set of reachable stops."""
    coverage_rows = coverage_rows or []
    stops = routing.network()[0]
    if origin not in stops:
        raise ValueError('Unknown origin stop')
    origin_problem = _coverage_problem(origin, coverage_rows)
    if origin_problem:
        return dict(status='unknown', scheduled=True, origin=origin, date=day,
                    reason=origin_problem, candidates=[], coverage=coverage_rows,
                    search=dict(complete=False, evaluated=0, unevaluated_count=0))

    outbound_deadline = min(home_by, earliest + outbound_budget)
    arrivals, paths = routing.scan(
        day, origin, earliest, outbound_deadline, mode=mode, radius=radius,
        buffer=buffer, feeds=feeds)
    ranked = sorted((arrival, sid) for sid, arrival in arrivals.items()
                    if sid != origin)
    selected = ranked[:limit]
    candidates = []
    for arrival, sid in selected:
        outbound = _scheduled_plan(arrival, paths.get(sid, ()), day, earliest,
                                   coverage_rows)
        candidates.append(evaluate(
            day, origin, sid, earliest, home_by, minimum_stay,
            outbound_budget, mode, radius, buffer, feeds, coverage_rows,
            outbound=outbound, latest_return=False))
    counts = {key: sum(item['status'] == key for item in candidates)
              for key in ('verified', 'ruled_out', 'unknown')}
    return dict(
        status='scheduled', scheduled=True, origin=origin, date=day,
        earliest_departure=earliest, home_by=home_by,
        minimum_stay=minimum_stay, outbound_budget=outbound_budget,
        candidates=candidates, counts=counts, coverage=coverage_rows,
        search=dict(complete=len(ranked) <= limit, evaluated=len(selected),
                    unevaluated_count=max(0, len(ranked) - limit), limit=limit,
                    note='Only evaluated stops receive a feasibility status.'),
    )


def last_service_departure(day, route_id, from_stop):
    """The last scheduled departure of a route from a stop on a day.

    Read from the imported connections every time — an anchor is a fact
    about the loaded schedule, never a hard-coded time. Returns None when
    the route does not depart that stop that day.
    """
    best = None
    final_arrival = {}
    for dep, arr, a, b, trip, route, head, pu, do, seq in routing.connections(day):
        if route != route_id:
            continue
        # connections(day) also carries the next service day's trips shifted
        # by +86400 (their ids are prefixed with that date). The anchor is
        # the requested day's own last service, plus its after-midnight tail.
        trip_day = trip.split('|', 1)[0] if '|' in trip else None
        if trip_day is not None and trip_day != day:
            continue
        if dep >= 86400 + 4 * 3600:
            continue
        final_arrival[trip] = arr  # rows are sequence-ordered; last write is the terminus
        if a == from_stop and pu == 0 and (best is None or dep > best['departure']):
            best = dict(route=route_id, trip=trip, headsign=head,
                        from_stop=from_stop, departure=dep)
    if best is None:
        return None
    best['final_arrival'] = final_arrival.get(best['trip'])
    return best


def plan_day(day, origin, visits, start, dwell=1800, anchor=None, home_by=86399,
             mode='walk', radius=500, buffer=300, feeds=(), coverage_rows=None):
    """Compose an ordered day of visits behind a protected return anchor.

    The anchor is either pinned — ``anchor=dict(route=..., from_stop=...)``,
    the last departure of that route from that stop, read from the schedule —
    or derived: the last viable return home from the final visit. A visit leg
    is accepted only if, after the minimum dwell at that visit, a certified
    path back to the anchor boarding stop still arrives by the anchor
    departure (less the transfer buffer as safety margin). A leg that would
    break the anchor is refused with the reason, never silently planned; the
    legs composed before it stand as a partial day.
    """
    coverage_rows = coverage_rows or []
    stops = routing.network()[0]
    for stop in [origin, *visits]:
        if stop not in stops:
            raise ValueError(f'Unknown stop: {stop}')
    opts = dict(mode=mode, radius=radius, buffer=buffer, feeds=feeds)
    result = dict(status='unknown', scheduled=True, date=day, origin=origin,
                  visits=list(visits), earliest_departure=start, home_by=home_by,
                  minimum_dwell=dwell, legs=[], dwells=[], coverage=coverage_rows)

    # --- Resolve and certify the anchor -------------------------------------
    if anchor and anchor.get('route'):
        anchor_stop = anchor.get('from_stop') or (visits[-1] if visits else origin)
        service = last_service_departure(day, anchor['route'], anchor_stop)
        if service is None:
            result.update(status='ruled_out', reason=dict(
                code='anchor_service_not_found',
                message=f"No departure of {anchor['route']} from {anchor_stop} exists in the loaded schedule for this date, so the pinned anchor cannot be protected."))
            return result
        anchor_departure = service['departure']
        anchor_home = routing.plan(day, anchor_stop, origin, anchor_departure,
                                   home_by, **opts)
        certified = bool(anchor_home.get('found')) and anchor_home['departure'] == anchor_departure
        anchor_info = dict(kind='pinned_service', route=anchor['route'],
                           trip=service['trip'], headsign=service['headsign'],
                           from_stop=anchor_stop, departure=anchor_departure,
                           certified=certified,
                           home_arrival=anchor_home.get('arrival') if certified else None)
        if not certified:
            result.update(status='unknown', reason=dict(
                code='anchor_not_homeward',
                message='The pinned last service does not itself start a certified journey home at its departure time, so it cannot serve as the return anchor.'),
                anchor=anchor_info)
            return result
    else:
        anchor_stop = visits[-1] if visits else origin
        latest_home = routing.latest(day, anchor_stop, origin, start, home_by, **opts)
        if not latest_home.get('found'):
            problem = _incomplete_coverage(coverage_rows)
            result.update(status='unknown' if problem else 'ruled_out',
                          reason=problem or dict(
                              code='no_viable_return',
                              message='No scheduled return home exists from the final stop within the day, so no anchor can be protected.'))
            return result
        anchor_departure = latest_home['departure']
        anchor_info = dict(kind='last_viable_return', route=None, trip=None,
                           headsign=None, from_stop=anchor_stop,
                           departure=anchor_departure, certified=True,
                           home_arrival=latest_home['arrival'])

    result['anchor'] = anchor_info
    # What happens if the anchor is missed — stated up front, from the data.
    after = routing.plan(day, anchor_stop, origin, anchor_departure + 1, home_by, **opts)
    result['if_missed'] = dict(
        found=bool(after.get('found')),
        departure=after.get('departure') if after.get('found') else None,
        arrival=after.get('arrival') if after.get('found') else None,
        message=('The next way home after the anchor is the departure above.'
                 if after.get('found') else
                 'There is no later return home in the loaded schedule that day. Missing the anchor means no scheduled way home.'))

    # --- Compose the day, protecting the anchor at every step ---------------
    current, now = origin, start
    for index, visit in enumerate(visits):
        leg = routing.plan(day, current, visit, now, home_by, **opts)
        if not leg.get('found'):
            result.update(status='partial' if result['legs'] else 'ruled_out',
                          refused_visit=visit, reason=dict(
                              code='no_leg_to_visit',
                              message=f'No scheduled itinerary reaches {visit} from {current} in the remaining day.'))
            return result
        arrival = leg['arrival']
        ready = arrival + dwell
        if visit == anchor_stop:
            back_ok = ready <= anchor_departure
            back_arrival = None
        else:
            back = routing.plan(day, visit, anchor_stop, ready, anchor_departure, **opts)
            back_ok = bool(back.get('found')) and back['arrival'] <= anchor_departure - buffer
            back_arrival = back.get('arrival') if back.get('found') else None
        if not back_ok:
            result.update(status='partial' if result['legs'] else 'anchor_protected',
                          refused_visit=visit, reason=dict(
                              code='would_break_anchor',
                              message=(f'Visiting {visit} (arrive {arrival}, ready to move on at {ready} after the minimum dwell) '
                                       f'leaves no certified path back to the anchor stop by {anchor_departure - buffer}. '
                                       'The leg was refused to protect the anchor, not planned anyway.'),
                              ready=ready, anchor_departure=anchor_departure,
                              back_arrival=back_arrival))
            return result
        result['legs'].append(dict(kind='visit', to=visit, plan=leg))
        current, now = visit, ready

    # --- Final approach to the anchor, then the anchor home -----------------
    if current != anchor_stop:
        approach = routing.plan(day, current, anchor_stop, now, anchor_departure, **opts)
        if not approach.get('found'):
            result.update(status='partial', reason=dict(
                code='anchor_unreachable_after_visits',
                message='The composed visits leave no certified path to the anchor stop, despite the per-visit checks.'))
            return result
        result['legs'].append(dict(kind='anchor_approach', to=anchor_stop, plan=approach))
        anchor_arrival = approach['arrival']
    else:
        anchor_arrival = result['legs'][-1]['plan']['arrival'] if result['legs'] else start
    home_plan = routing.plan(day, anchor_stop, origin, anchor_departure, home_by, **opts)
    result['legs'].append(dict(kind='anchor_home', to=origin, plan=home_plan))
    result['slack_seconds'] = anchor_departure - anchor_arrival
    result['home_arrival'] = home_plan.get('arrival')

    # Dwell windows: from each visit's arrival until the next leg departs.
    points = [(leg['plan']['arrival'], leg['to']) for leg in result['legs'] if leg['kind'] == 'visit']
    departures = [leg['plan']['departure'] for leg in result['legs'][1:]] + [anchor_departure]
    for (arrive, stop), leave in zip(points, departures):
        result['dwells'].append(dict(stop=stop, arrive=arrive, depart=leave,
                                     seconds=max(0, leave - arrive)))
    result['status'] = 'composed'
    result['reason'] = dict(code='day_composed',
                            message='Every visit is composed with the return anchor protected.')
    return result
