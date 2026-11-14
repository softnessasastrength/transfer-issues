"""Percival Mobility Bubble: where can I go AND get back within a budget?

Built on the same connection-scan data as routing.scan. A destination counts
as reachable only when (a) the outbound scan reaches it within the budget and
(b) a feasible return to the origin exists that arrives home by the end of
the budget window (after the requested visit time at the destination).

Classification is three-way and evidence-based:
- reachable: outbound found AND return feasible within the window.
- unreachable: the loaded data was sufficient to evaluate the stop and one of
  the two conditions failed (reason recorded per stop in aggregate counts).
- unknown: the stop or area could not be evaluated from loaded data at all
  (its feed is missing, failed to download, or out of its service period on
  the requested date). Missing data is never reported as "unreachable".

All times are service-day seconds in America/New_York, matching API.md.
Ground links are the router's straight-line x1.3 estimates, not street paths.
"""
import routing

DEFAULT_BUDGET = 3600  # 60 minutes, per the Percival Mobility Bubble brief


def latest_return_departures(day, home, deadline, mode='walk', radius=500,
                             buffer=300, feeds=()):
    """Latest feasible departure time from every stop that still gets you
    home by `deadline`, computed with one reverse connection scan.

    Returns {stop_id: latest_departure_seconds}. Waiting is allowed, so if
    the latest feasible departure from a stop is L, any ready time <= L can
    use that itinerary. Transfer buffer applies when changing vehicles, not
    when staying on the same trip, mirroring routing.scan semantics.
    """
    stops, _grid, rules = routing.network()
    if home not in stops:
        raise ValueError('Unknown origin stop')

    def propagate_walk(best, max_passes=12):
        # Being at a stop by time T and walking to a stop with a known
        # feasible departure extends feasibility backwards by the estimate.
        for _ in range(max_passes):
            changed = False
            for sid, latest in list(best.items()):
                for dest, seconds, _m in routing.neighbors(sid, radius, mode):
                    cand = latest - seconds
                    if cand > best.get(dest, -1):
                        best[dest] = cand
                        changed = True
            if not changed:
                break
        return best

    # Walking home needs no transfer buffer in routing.scan semantics:
    # ground legs depart at arrival time. walk_best[s] is the latest time
    # to be at s and still walk home by the deadline.
    walk_best = propagate_walk({home: deadline})
    best = dict(walk_best)
    good_from = {}  # trip -> earliest sequence from which the trip reaches home
    conns = [c for c in routing.connections(day)
             if not feeds or c[5].split(':')[0] in feeds]
    # Iterate to a fixpoint: a return may chain walk -> transit -> walk ->
    # transit, so transit segments must be re-examined after walk times
    # improve. good_from persists across rounds (it only ever grows).
    for _round in range(6):
        before = dict(best)
        for dep, arr, a, b, trip, route, head, pu, do, seq in reversed(conns):
            if arr > deadline:
                continue
            feasible = False
            if b == home:
                feasible = True
            elif good_from.get(trip) == seq + 1:
                feasible = True  # stay on the same vehicle; no buffer
            elif b in best and arr + buffer <= best[b]:
                feasible = True  # alight and board something else at b
            elif arr <= walk_best.get(b, -1):
                feasible = True  # alight at b and walk home
            if not feasible:
                continue
            good_from[trip] = seq
            if dep > best.get(a, -1):
                # Boarding at `a` at `dep` reaches home; prohibited pickups
                # and prohibited-transfer rules mirror routing.scan.
                rule = rules.get((a, a))
                if pu == 0 and not (rule and rule[0] == 3):
                    best[a] = dep
        propagate_walk(best)
        if best == before:
            break
    return best


def classify(day, origin, start, budget=DEFAULT_BUDGET, visit=0, mode='walk',
             radius=500, buffer=300, feeds=(), coverage_rows=None,
             source_rows=None):
    """Three-way Mobility Bubble classification for one origin/date/start."""
    stops, _grid, _rules = routing.network()
    if origin not in stops:
        raise ValueError('Unknown origin stop')
    deadline = start + budget
    arrivals, paths = routing.scan(day, origin, start, deadline, mode=mode,
                                   radius=radius, buffer=buffer, feeds=feeds)
    latest_back = latest_return_departures(day, origin, deadline, mode=mode,
                                           radius=radius, buffer=buffer,
                                           feeds=feeds)
    coverage_rows = coverage_rows if coverage_rows is not None else []
    source_rows = source_rows if source_rows is not None else []
    unevaluable_feeds = {row['feed'] for row in coverage_rows
                         if row.get('status') != 'imported'
                         or not row.get('in_service_period', True)}
    reachable, unreachable = [], []
    reasons = {'no_outbound_within_budget': 0, 'no_feasible_return': 0}
    unknown_stop_count = 0
    for sid, stop in stops.items():
        feed = sid.split(':')[0]
        if feed in unevaluable_feeds:
            unknown_stop_count += 1
            continue
        if sid not in arrivals:
            reasons['no_outbound_within_budget'] += 1
            unreachable.append(sid)
            continue
        ready = arrivals[sid] + visit
        if ready <= latest_back.get(sid, -1):
            legs = [dict(leg) for leg in paths.get(sid, ())]
            reachable.append(dict(
                id=sid, name=stop['name'], lat=stop['lat'], lon=stop['lon'],
                arrival=arrivals[sid], travel_seconds=arrivals[sid] - start,
                latest_return_departure=latest_back[sid], legs=legs))
        else:
            reasons['no_feasible_return'] += 1
            unreachable.append(sid)
    unknown_feeds = [dict(feed=s['id'], status=s.get('status'),
                          reason=s.get('refresh_error')
                          or ('out of service period on ' + day
                              if s.get('status') == 'imported'
                              else 'feed not loaded'))
                     for s in source_rows
                     if s['id'] in unevaluable_feeds
                     or s.get('status') != 'imported']
    evidence_sources = [dict(feed=s['id'], status=s.get('status'),
                             retrieved_at=s.get('retrieved_at'),
                             service_start=s.get('service_start'),
                             service_end=s.get('service_end'),
                             sha256=s.get('sha256'))
                        for s in source_rows]
    return dict(
        origin=origin, date=day, start=start, budget=budget, visit=visit,
        deadline=deadline, mode=mode,
        reachable=sorted(reachable, key=lambda r: (r['arrival'], r['id'])),
        unreachable_count=len(unreachable),
        unreachable_reasons=reasons,
        unknown=dict(feeds=unknown_feeds, stop_count=unknown_stop_count,
                     note='Destinations served only by these feeds cannot be '
                          'evaluated from loaded data. Unknown is not '
                          'evidence that no service exists.'),
        coverage=coverage_rows, sources=evidence_sources,
        status='Scheduled feasibility only, from published GTFS loaded in '
               'this atlas. Ground links are estimates. Not live service.')
