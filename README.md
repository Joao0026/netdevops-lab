# NetDevOps Home Lab

A virtualized enterprise network built with [Containerlab](https://containerlab.dev/), used as a
hands-on playground for applying Network-as-Code practices: automated configuration deployment,
Git-versioned device configs, and infrastructure monitoring.

**Status: In Progress** — this repo is being built incrementally, phase by phase (see below).

## Why this project

Coming from a Networking internship (firewall & QoS automation at Eurotux) and CCNA/Sophos
certifications, I wanted a repeatable, fully open-source environment to practice network
automation end-to-end — without relying on Cisco IOS licensing or GNS3/VM overhead. This lab
uses [FRRouting](https://frrouting.org/) (open-source router) in containers, orchestrated by
Containerlab.

## Topology

```
        10.0.13.0/30
   r1 ─────────────────── r3
   │                        │
   │ 10.0.12.0/30           │ 10.0.23.0/30
   │                        │
   └──────── r2 ────────────┘

192.168.1.0/24 ── r1        r3 ── 192.168.3.0/24
      pc1                          pc3
```

- **r1, r2, r3**: FRRouting containers running OSPF (area 0), forming a triangle so there's a
  redundant path between r1 and r3 (used later to test failover).
- **pc1, pc3**: lightweight test hosts (`wbitt/network-multitool`) at each end of the network,
  used to validate end-to-end reachability.

## Requirements

- Docker
- [Containerlab](https://containerlab.dev/install/) (`bash -c "$(curl -sL https://get.containerlab.dev)"`)

## Deploy

```bash
git clone <this-repo>
cd netdevops-lab
sudo containerlab deploy -t topology.clab.yml
```

## Verify

```bash
# Check OSPF neighbors on r1
docker exec -it clab-netdevops-lab-r1 vtysh -c "show ip ospf neighbor"

# Check the routing table learned via OSPF
docker exec -it clab-netdevops-lab-r1 vtysh -c "show ip route ospf"

# End-to-end connectivity test
docker exec -it clab-netdevops-lab-pc1 ping -c 4 192.168.3.10
```

## Destroy

```bash
sudo containerlab destroy -t topology.clab.yml
```

## Roadmap

- [x] **Phase 1 — Base topology**: FRR routers + OSPF, verified end-to-end connectivity via
      Containerlab.
- [ ] **Phase 2 — Automation**: Ansible playbook to push interface/OSPF config changes to all
      routers from a single YAML source of truth, instead of editing `frr.conf` by hand.
- [ ] **Phase 3 — Config as Code**: Python script that snapshots running configs from all
      routers on a schedule and commits them to this repo (config drift / audit trail).
- [ ] **Phase 4 — Monitoring**: Prometheus + Grafana + `snmp_exporter` dashboard showing
      interface traffic and OSPF neighbor state.
- [ ] **Phase 5 — Failure testing**: script that disables a link (`docker network disconnect`)
      and measures OSPF reconvergence time.

## Skills demonstrated

Networking (OSPF, routing/switching fundamentals), Linux, containerized network labs
(Containerlab), Infrastructure as Code — building on QoS/firewall automation experience from
the Eurotux internship.
