#!/usr/bin/env python3
"""Latency profiler for the Atlas planning endpoints (M0, stdlib only).

Reproduces the baseline recorded in CODEX_HANDOFF.md under
"Latency profile (Ember, 2026-11-14)". Run from the repo root after
`python3 scripts/prepare_data.py`:

    python3 scripts/profile_latency.py

It times, in-process on the full loaded dataset for Tuesday 2026-11-17:
the per-day connection-list build and the stop-network build (cold,
cache-cleared), the forward connection scan, single plans (intercity and
local), the return=1 composite the server performs (outbound plan +
return plan + latest-return binary search), and the Mobility Bubble
reverse scan and full classification. It finishes with cProfile summaries
for the scan and the bubble reverse scan. Absolute numbers depend on the
machine; the phase ranking is the durable part.
"""
import cProfile
import io
import json
import pathlib
import pstats
import statistics
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import bubble
import database as db
import routing

DAY = '2026-11-17'
START = 28800  # 08:00 service-day seconds
DEADLINE = 86399
HARTFORD = 'hartford:6'
SPRINGFIELD = 'pvta:5101'
COURT_SQUARE = 'pvta:1495'


def timed(label, fn, repeats=1):
    runs = []
    for _ in range(repeats):
        t = time.perf_counter()
        fn()
        runs.append(time.perf_counter() - t)
    med = statistics.median(runs)
    print(f'{label}: median {med:.2f}s '
          f'(runs: {", ".join(f"{r:.2f}" for r in runs)})')
    return med


def profile(label, fn, top=8):
    pr = cProfile.Profile()
    pr.enable()
    fn()
    pr.disable()
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats('tottime').print_stats(top)
    lines = [ln for ln in s.getvalue().splitlines()
             if 'function calls' in ln or '{' in ln or ':' in ln]
    print(f'--- cProfile {label} (top by tottime) ---')
    for ln in lines[:top + 2]:
        print('   ', ln.rstrip())


def main():
    print(f'== Atlas latency profile, {DAY}, full loaded dataset ==')
    # Cold builds: caches cleared before every run.
    def cold_connections():
        db.connections.cache_clear()
        db.connections(DAY)
    timed('connections(day) build, cold', cold_connections, 3)
    n = len(db.connections(DAY))
    print(f'    ({n} connections in the service-day list)')

    def cold_network():
        routing.network.cache_clear()
        routing.neighbors.cache_clear()
        routing.network()
    timed('network() build, cold', cold_network, 3)

    # Forward scan: first with an empty neighbors cache, then warm.
    routing.neighbors.cache_clear()
    timed('scan Hartford full-day, neighbors cold',
          lambda: routing.scan(DAY, HARTFORD, START, DEADLINE), 2)
    timed('scan Hartford full-day, warm',
          lambda: routing.scan(DAY, HARTFORD, START, DEADLINE), 5)
    print('   ', routing.neighbors.cache_info())

    timed('plan Hartford->Springfield, warm',
          lambda: routing.plan(DAY, HARTFORD, SPRINGFIELD, START, DEADLINE),
          5)
    timed('plan Springfield->Court Square (local), warm',
          lambda: routing.plan(DAY, SPRINGFIELD, COURT_SQUARE, START,
                               DEADLINE), 5)

    out = routing.plan(DAY, HARTFORD, SPRINGFIELD, START, DEADLINE)
    ready = out['arrival'] + 3600

    def composite():
        routing.plan(DAY, HARTFORD, SPRINGFIELD, START, DEADLINE)
        routing.plan(DAY, SPRINGFIELD, HARTFORD, ready, DEADLINE)
        routing.latest(DAY, SPRINGFIELD, HARTFORD, ready, DEADLINE)
    timed('return=1 composite (plan + return plan + latest), warm',
          composite, 3)
    timed('latest() alone, warm',
          lambda: routing.latest(DAY, SPRINGFIELD, HARTFORD, ready,
                                 DEADLINE), 3)

    timed('bubble latest_return_departures (deadline = start+3600)',
          lambda: bubble.latest_return_departures(DAY, HARTFORD,
                                                  START + 3600), 3)
    cov, src = db.coverage(DAY), db.sources()
    timed('bubble classify, full',
          lambda: bubble.classify(DAY, HARTFORD, START, budget=3600,
                                  visit=0, coverage_rows=cov,
                                  source_rows=src), 3)
    result = bubble.classify(DAY, HARTFORD, START, budget=3600, visit=0,
                             coverage_rows=cov, source_rows=src)
    print(f'    (bubble response JSON: '
          f'{len(json.dumps(result)) / 1024:.0f} KiB, '
          f'{len(result["reachable"])} reachable stops)')

    profile('routing.scan, warm caches',
            lambda: routing.scan(DAY, HARTFORD, START, DEADLINE))
    profile('bubble.latest_return_departures',
            lambda: bubble.latest_return_departures(DAY, HARTFORD,
                                                    START + 3600))


if __name__ == '__main__':
    main()
