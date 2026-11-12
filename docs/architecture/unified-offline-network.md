# Step 1: unified offline transit network (draft)

Architecture choice **B**: Python is the Mac mini data-preparation and LAN test backend; Kotlin will eventually own offline Android journey calculations.

`scripts/assemble_offline_network.py` combines **explicitly selected** and verified agency SQLite files into one SQLite network while retaining GTFS namespaced IDs. It validates source checksums, schema, agency isolation, duplicate keys and key references, writes to a temporary file and atomically replaces the requested output only on success. It does not modify individual packs or personal history.

## Example

First import official GTFS into `data/atlas.sqlite`, then:

```bash
python3 scripts/build_lan_packs.py
python3 scripts/assemble_offline_network.py --agencies cttransit hartford amtrak --output build/offline-network/atlas.sqlite
python3 -m unittest tests.test_unified_network -v
```

**PVTA:** add `pvta` only if a validated source is present in the generated catalog. Missing agencies cause an explicit error; they are not silently skipped.

The resulting database uses the existing `stops`, `routes`, `trips`, `times`, `calendar`, `exceptions`, `shapes` and `transfers` schema plus `network_packs` provenance records. It is intended as an intermediate offline routing input. The existing LAN browser planner still reads its configured database, not automatically this newly assembled file.

## Constraints and next step

- The assembler **does not** download or activate unselected agencies, nor infer interagency transfers from proximity.
- Only explicitly published transfers are retained. Cross-agency transfer candidates require a separate decision about proximity, station identity, pedestrian paths, and realistic buffers.
- No street graph, native Android connection-scan engine, complete offline map, or production-signed catalog yet.
- Some source packs may have incompatible schema or non-namespaced overlapping identifiers; fail closed rather than silently merge inconsistent records.
- Tests are synthetic and committed but not executed in this session; device tests and real-feed integration are outstanding.
- Existing `offline_packages.py`, `lan_server.py`, `atlas-lan.sh`, browser planner and Android test client are preserved.

Next decision: how to discover interagency transfer candidates before real pedestrian graph data is available.
