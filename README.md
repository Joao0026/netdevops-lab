# NetDevOps Lab

A hands-on Network Automation lab built with Docker, Containerlab, FRRouting, Ansible and Python.

This project demonstrates how traditional networking concepts such as OSPF, routing redundancy and end-to-end connectivity can be combined with DevOps practices like Infrastructure as Code, Git versioning, automation and configuration snapshots.

## Project Status

The lab currently includes:

- Phase 1: Base OSPF topology with end-to-end connectivity
- Phase 2: Ansible-generated router configuration from a single source of truth
- Phase 3: Python-based running-config snapshots
- Phase 5: OSPF failover testing and recovery measurement

Phase 4, monitoring with Prometheus and Grafana, is planned next.

## What This Project Demonstrates

- Building reproducible network labs with Containerlab and Docker
- Configuring dynamic routing with FRRouting and OSPF
- Managing router configuration as code with Ansible
- Using a YAML source of truth to generate network device configs
- Capturing running configurations for audit and drift detection
- Testing OSPF failover and routing convergence
- Using Git to track infrastructure and network changes

## Why I Built This

I created this project to strengthen my practical skills in Network Automation and NetDevOps.

After working with firewall and QoS automation during my networking internship, I wanted to build a fully reproducible lab where I could practice routing, automation and infrastructure documentation without relying on licensed network images or heavy virtual machines.

This lab uses open-source tools and can be recreated from the files in this repository.

## Topology

The lab uses three FRRouting routers connected in a triangle. This creates redundant OSPF paths between the two end hosts.

```text
        10.0.13.0/30
   r1 ------------------- r3
   |                       |
   | 10.0.12.0/30          | 10.0.23.0/30
   |                       |
   -------- r2 ------------

192.168.1.0/24 -- r1      r3 -- 192.168.3.0/24
      pc1                         pc3
```

## Components

- `r1`, `r2`, `r3`: FRRouting containers running OSPF area 0
- `pc1`, `pc3`: lightweight Linux test hosts used to validate connectivity
- `topology.clab.yml`: Containerlab topology definition
- `configs/`: generated FRR configuration files
- `ansible/`: source of truth, templates and playbook for router configuration
- `scripts/`: automation scripts for snapshots and failover testing
- `snapshots/`: captured running configurations
- `results/`: generated test results

## Technologies Used

- Docker
- Containerlab
- FRRouting
- OSPF
- Ansible
- Python
- Linux networking
- YAML
- Git

## Current Features

- Three-router routed topology
- OSPF adjacency between all routers
- Redundant path between `r1` and `r3`
- End-to-end connectivity between `pc1` and `pc3`
- Router configuration generated with Ansible
- Running-config snapshots collected with Python
- OSPF failover test script
- Git-versioned infrastructure and network configuration

## Requirements

- Docker
- Containerlab
- Ansible
- Python 3
- WSL or Linux environment

## Deploy The Lab

```bash
sudo containerlab deploy -t topology.clab.yml
```

## Verify OSPF

```bash
docker exec clab-netdevops-lab-r1 vtysh -c "show ip ospf neighbor"
docker exec clab-netdevops-lab-r2 vtysh -c "show ip ospf neighbor"
docker exec clab-netdevops-lab-r3 vtysh -c "show ip ospf neighbor"
```

## Test End-To-End Connectivity

```bash
docker exec clab-netdevops-lab-pc1 ping -c 4 192.168.3.10
docker exec clab-netdevops-lab-pc3 ping -c 4 192.168.1.10
```

## Generate Router Configs With Ansible

Router data is stored in:

```text
ansible/vars/routers.yml
```

Generate FRR configs from the source of truth:

```bash
ansible-playbook -i ansible/inventory.yml ansible/playbook.yml
```

This renders:

```text
configs/r1/frr.conf
configs/r2/frr.conf
configs/r3/frr.conf
```

## Snapshot Running Configs

Capture the real running configuration from all routers:

```bash
python3 scripts/snapshot_configs.py
```

The latest snapshots are written to:

```text
snapshots/latest/
```

Snapshot and create a Git commit when there are changes:

```bash
python3 scripts/snapshot_configs.py --commit
```

## Test OSPF Failover

The failover script disables the direct `r1-r3` link, checks whether traffic recovers through `r2`, restores the link and writes a report.

```bash
python3 scripts/test_failover.py
```

Latest result:

```text
Traffic recovered after 1.425 seconds.
```

The report is written to:

```text
results/failover-latest.txt
```

## Destroy The Lab

```bash
sudo containerlab destroy -t topology.clab.yml --cleanup
```

## Roadmap

- [x] Phase 1: Base topology with FRRouting and OSPF
- [x] Phase 2: Ansible automation for router configuration
- [x] Phase 3: Automated running-config snapshots
- [ ] Phase 4: Monitoring with Prometheus, Grafana and SNMP exporter
- [x] Phase 5: OSPF failover testing and recovery measurement

## Skills Highlighted

This project highlights practical skills in networking, Linux, routing protocols, containerized network labs, Infrastructure as Code, configuration management, automation scripting and Git-based infrastructure tracking.

It is designed as a portfolio project to demonstrate hands-on learning in NetDevOps and Network Automation.
