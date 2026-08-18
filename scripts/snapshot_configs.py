#!/usr/bin/env python3
"""Snapshot running FRR configs from the lab routers.

Run this script from WSL while the Containerlab topology is running.
By default it only writes files under snapshots/latest/. Use --commit to
create a Git commit when the snapshot changes.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ROUTERS = ("r1", "r2", "r3")


def run_command(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def normalize_running_config(output: str) -> str:
    """Keep the actual FRR config and drop vtysh status/warning lines."""
    lines: list[str] = []
    capture = False

    for raw_line in output.splitlines():
        line = raw_line.rstrip()

        if line.startswith("% Can't open configuration file"):
            continue
        if line == "Building configuration...":
            continue
        if line == "Current configuration:":
            capture = True
            continue

        if capture or line.startswith("!") or line.startswith("frr version"):
            lines.append(line)

    if not lines:
        lines = [line.rstrip() for line in output.splitlines() if line.strip()]

    return "\n".join(lines).strip() + "\n"


def snapshot_router(lab_name: str, router: str) -> str:
    container_name = f"clab-{lab_name}-{router}"
    result = run_command(
        ["docker", "exec", container_name, "vtysh", "-c", "show running-config"]
    )
    return normalize_running_config(result.stdout + result.stderr)


def git_has_changes(path: Path) -> bool:
    result = run_command(["git", "status", "--porcelain", "--", str(path)], check=False)
    return bool(result.stdout.strip())


def commit_snapshot(snapshot_dir: Path) -> None:
    run_command(["git", "add", str(snapshot_dir)])

    if not git_has_changes(snapshot_dir):
        print("No snapshot changes to commit.")
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    run_command(["git", "commit", "-m", f"Snapshot router configs ({timestamp})"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Snapshot running FRR configs from Containerlab.")
    parser.add_argument("--lab-name", default="netdevops-lab", help="Containerlab lab name.")
    parser.add_argument("--output-dir", default="snapshots/latest", help="Snapshot output directory.")
    parser.add_argument("--commit", action="store_true", help="Commit snapshot changes to Git.")
    parser.add_argument(
        "--routers",
        nargs="+",
        default=list(DEFAULT_ROUTERS),
        help="Router names to snapshot.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    snapshot_dir = repo_root / args.output_dir
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for router in args.routers:
        try:
            config = snapshot_router(args.lab_name, router)
        except subprocess.CalledProcessError as error:
            print(f"Failed to snapshot {router}: {error.stderr.strip()}", file=sys.stderr)
            return error.returncode

        destination = snapshot_dir / f"{router}.conf"
        destination.write_text(config, encoding="utf-8", newline="\n")
        print(f"Wrote {destination.relative_to(repo_root)}")

    if args.commit:
        commit_snapshot(snapshot_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
