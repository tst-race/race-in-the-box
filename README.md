# RACE in the Box (RiB)

Race in the Box (Rib) is a collection of Docker containers, scripts, configurations, that enable repeatable builds, and facilitates quick deployments, and testing of the RACE system. RiB by itself will contain a fully stubbed, insecure version of the RACE system. The purpose of this is to allow for independent development of components without the need to wait for other performers.

As we begin to build out RiB, things will be more manual and less configurable initially. This will change and become easier to configure, build, test, and run in the future.

## Table of Contents

* [Dependencies](#dependencies)
* [Prerequisites](#prerequisites)
* [Modes](#Modes)
* [How To](#how-to)
* [Command Groups](#command-groups)
* [Scripts](#scripts)
* [Notes](#notes)
* [TODO](#todo)

## Dependencies/System Requirements

Dependencies for the RiB system to run on a local machine. RiB is run inside a docker contiainer on the user's machine.

### Hardware Requirements

* Windows 10 (with Subsystem for Linux)
    * 4 CPU
    * 4 GB RAM
* Linux
    * 4 CPU
    * 4 GB RAM
* Mac OSX
    * 4 CPU
    * 4 GB RAM

### Applications/Packages (On Host Machine)

* docker

## Prerequisites

### Docker (And GitHub Container Registry)

If using a private repository for race-in-the-box, users must log into the
GitHub Docker Container Registy

```
localhost$ docker login ghcr.io -u {GITHUB_USERNAME}
>> Password: {GITHUB_TOKEN}
```

## RiB/Deployment Modes

There are two RiB modes that RiB can operate in when working with deployments:

* Local - RiB Developer is intended to be deployed on developer laptops
* AWS - RiB Integration is intended to be deployed in AWS at a reasonable scale to test integration progress.

Each deployment mode has it's own set of commands under its own command group
(e.g., `rib deployment local {action}`).

The `rib-use {mode} {deployment_name}` command can set a default mode and
deployment to enable "shortcut" commands. These shortcut commands do not require
the mode or `--name` option.

```
1) rib:2.0.0@code# rib deployment local status --name=my-local-deployment-name
Deployment my-local-deployment-name apps are started
1) rib:2.0.0@code# rib-use local my-local-deployment-name
1) rib:dev:local:my-local-deployment-name@code# rib deployment status
Deployment my-local-deployment-name apps are started
```

## How To

### How To Run Manual Deployment Tests

Guide found [here](./documentation/how-to/manual-deployment-test.md)

### How To Run Automated Deployment Tests

Guide found [here](./documentation/how-to/automated-deployment-test.md)

### How To Run Automated Network Manager Integration Tests

Guide found [here](./documentation/how-to/automated-network-manager-integration-test.md)

### How To Run Automated Comms Channel Integration Tests

Guide found [here](./documentation/how-to/automated-ta2-integration-test.md)

### How To Run Node Bootstrap Tests

Guide found [here](./documentation/how-to/node-bootstrap-test.md)

### How to check the deployment that a container belongs to

Note that if running on Linux you may need to use `sudo`.

```bash
docker inspect --format '{{ index .Config.Labels "race.rib.deployment-name"}}' <CONTAINER_NAME>
docker inspect --format '{{.Name}}        {{ index .Config.Labels "race.rib.deployment-name"}}' $(docker ps -aq)
```

Example:

```bash
$ docker inspect --format '{{ index .Config.Labels "race.rib.deployment-name"}}' race-client-1
my-deployment-name
```

To get the name of the deployment running without specifying a container name then use this command.

```bash
docker inspect --format '{{ index .Config.Labels "race.rib.deployment-name"}}' $(docker ps -aq) | uniq | grep -v -e '^$'
```

## Commands

RACE in the Box is a command line tool that is broken down into command groups. Each
command group responsble for a set of functionality grouped by functionality.

Run `rib --help` to see all available command groups and `rib <group> --help` to
see all available commands within a group.

Additionally, the `rib help` command provides more detailed documentation for
commands and concepts, similar to Unix manpages. Run `rib help -a` to see all
documented commands and `rib help -g` to see all available guides.

## Scripts

Scripts are automated functionality that is external to RiB. Some of these scripts are
called automatically from RiB (i.e. `rib.sh` calls `initialize_rib_state.py`) when it starts
the docker container.

### [`initialize_rib_state.py`](scripts/internal/initialize_rib_state.py)

```
Purpose:
    Script responsible for initalizing the RACE environment

Steps:
    - Check to see if the system is initalized
    - Make dirs if necessary
    - Return/Exit

Example Call:
    python3 /race_in_the_box/rib/scripts/internal/initialize_rib_state.py
```

## Notes

* Updated design for phase 2, updates to commands have been made. If you experience any issues, please reach out to Two Six Labs

## TODO

* Phase 2 improvements
