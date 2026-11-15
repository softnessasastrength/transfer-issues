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
