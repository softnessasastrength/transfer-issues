# Offline package manager proof of concept

The stdlib-only `offline_packages.py` module provides a local backend for **Choose Your Transit Network**. It does not yet provide an Android UI, network downloader, authenticated remote catalog, offline basemap or pedestrian graph. It does not assert that PVTA or other agency datasets are currently available.

## Usage

From the repository root:

```python
from offline_packages import OfflinePackManager
manager = OfflinePackManager("build/offline-store")
# catalog = {"packages": {"ct": {"id":"ct","kind":"agency",
#   "agency":"cttransit","version":"1","bytes":123,
#   "sha256":"<actual digest>","dependencies":[]}}}
# plan = manager.plan(catalog, ["cttransit"])
# Display plan to the user and obtain explicit approval first.
# manager.install(catalog, ["cttransit"], {"ct":"path/to/verified-pack"},
#                 approved=True, update_policy="auto")
```

**Do not treat a synthetic catalog as an authenticated catalog.** The POC validates file size, SHA-256, and optionally SQLite integrity, but does not establish trust in the manifest signer. Real deployment requires a pinned/trusted catalog key or equivalent authenticated provenance and full pack compatibility checks.

Current features: selected-agency dependency resolution, no cross-agency surprise dependencies, shared dependency deduplication, reviewable byte totals, explicit approval gate, local-only copy/staging, checksum verification, content-addressed payloads, atomic state activation, installed verification, and update eligibility that refuses new dependencies. No automatic network access.

Limitations: installer copies verified files but does not download them; no download resume, durable transaction journal, crash-time cleanup/rollback workflow, full dependency removal, pack garbage collection, catalog signatures, disk quota planning, app-facing API or native device tests. Automatic update policy is persisted and eligibility can be queried, but **no scheduler or automatic download** exists. Existing files remain for rollback; unused files are not pruned. Agency selection in state is replaced only on explicit approved install. This is an engineering proof of concept, not complete production package management.

Run synthetic tests with `python -m unittest tests.test_offline_packages -v`. All tests use fake payload bytes and no network.
