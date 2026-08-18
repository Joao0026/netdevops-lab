# Configuration Snapshots

This directory stores running configuration snapshots collected from the lab routers.

The latest snapshot is written to:

```text
snapshots/latest/
```

Generate a snapshot while the lab is running:

```bash
python3 scripts/snapshot_configs.py
```

Generate and commit the snapshot when there are changes:

```bash
python3 scripts/snapshot_configs.py --commit
```
