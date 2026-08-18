#!/usr/bin/env python3
"""Test OSPF failover by disabling and restoring a lab interface.

Default test:
  - disables r1 eth2, the direct r1-r3 link
  - pings pc3 from pc1 until traffic succeeds again
  - restores r1 eth2
  - writes a short report to results/failover-latest.txt
"""

from __future__ import annotations

import argparse
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def run_command(command: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def docker_exec(container: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    return run_command(["docker", "exec", container, *command])


def container_name(lab_name: str, node: str) -> str:
    return f"clab-{lab_name}-{node}"


def show_route(lab_name: str, router: str, target: str) -> str:
    result = docker_exec(
        container_name(lab_name, router),
        ["vtysh", "-c", f"show ip route {target}"],
    )
    return (result.stdout + result.stderr).strip()


def single_ping(lab_name: str, source: str, target: str) -> bool:
    result = docker_exec(
        container_name(lab_name, source),
        ["ping", "-c", "1", "-W", "1", target],
    )
    return result.returncode == 0


def set_interface_state(lab_name: str, router: str, interface: str, state: str) -> None:
    result = docker_exec(
        container_name(lab_name, router),
        ["ip", "link", "set", interface, state],
    )

    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout).strip())


def run_failover_test(args: argparse.Namespace) -> dict[str, object]:
    route_before = show_route(args.lab_name, args.router, args.route_target)
    baseline_ok = single_ping(args.lab_name, args.source, args.target)

    attempts: list[dict[str, object]] = []
    start = time.monotonic()

    try:
        set_interface_state(args.lab_name, args.router, args.interface, "down")
        time.sleep(args.initial_wait)

        recovered_at: float | None = None
        deadline = time.monotonic() + args.timeout

        while time.monotonic() < deadline:
            elapsed = time.monotonic() - start
            success = single_ping(args.lab_name, args.source, args.target)
            attempts.append({"elapsed": round(elapsed, 3), "success": success})

            if success:
                recovered_at = elapsed
                break

            time.sleep(args.interval)

        route_during_failure = show_route(args.lab_name, args.router, args.route_target)
    finally:
        set_interface_state(args.lab_name, args.router, args.interface, "up")

    time.sleep(args.restore_wait)
    route_after_restore = show_route(args.lab_name, args.router, args.route_target)
    restored_ok = single_ping(args.lab_name, args.source, args.target)

    return {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "lab_name": args.lab_name,
        "failed_link": f"{args.router}:{args.interface}",
        "source": args.source,
        "target": args.target,
        "baseline_ok": baseline_ok,
        "recovered_at": recovered_at,
        "restored_ok": restored_ok,
        "attempts": attempts,
        "route_before": route_before,
        "route_during_failure": route_during_failure,
        "route_after_restore": route_after_restore,
    }


def write_report(report: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    attempts = report["attempts"]
    assert isinstance(attempts, list)

    lines = [
        "# OSPF Failover Test",
        "",
        f"Timestamp: {report['timestamp']}",
        f"Lab: {report['lab_name']}",
        f"Failed link: {report['failed_link']}",
        f"Traffic test: {report['source']} -> {report['target']}",
        f"Baseline ping before failure: {'ok' if report['baseline_ok'] else 'failed'}",
        f"Ping after restore: {'ok' if report['restored_ok'] else 'failed'}",
        "",
    ]

    if report["recovered_at"] is None:
        lines.append("Result: traffic did not recover before timeout.")
    else:
        lines.append(f"Result: traffic recovered after {report['recovered_at']:.3f} seconds.")

    lines.extend(
        [
            "",
            "## Ping Attempts During Failure",
            "",
        ]
    )

    for attempt in attempts:
        status = "ok" if attempt["success"] else "failed"
        lines.append(f"- t+{attempt['elapsed']}s: {status}")

    lines.extend(
        [
            "",
            "## Route Before Failure",
            "",
            "```text",
            str(report["route_before"]),
            "```",
            "",
            "## Route During Failure",
            "",
            "```text",
            str(report["route_during_failure"]),
            "```",
            "",
            "## Route After Restore",
            "",
            "```text",
            str(report["route_after_restore"]),
            "```",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test OSPF failover in the Containerlab topology.")
    parser.add_argument("--lab-name", default="netdevops-lab")
    parser.add_argument("--router", default="r1", help="Router where the interface will be disabled.")
    parser.add_argument("--interface", default="eth2", help="Interface to disable during the test.")
    parser.add_argument("--source", default="pc1", help="Source host used for ping tests.")
    parser.add_argument("--target", default="192.168.3.10", help="Destination IP used for ping tests.")
    parser.add_argument("--route-target", default="192.168.3.0/24", help="Route to inspect on the router.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Maximum seconds to wait for recovery.")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between ping attempts.")
    parser.add_argument("--initial-wait", type=float, default=1.0, help="Seconds to wait after link failure.")
    parser.add_argument("--restore-wait", type=float, default=5.0, help="Seconds to wait after restoring link.")
    parser.add_argument("--output", default="results/failover-latest.txt", help="Report output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output_path = repo_root / args.output

    report = run_failover_test(args)
    write_report(report, output_path)

    print(f"Wrote {output_path.relative_to(repo_root)}")

    if report["recovered_at"] is None:
        print("Traffic did not recover before timeout.")
        return 1

    print(f"Traffic recovered after {report['recovered_at']:.3f} seconds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
