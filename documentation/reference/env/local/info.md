# Info about the Local Environment

The purpose of this command is to understand the configurations of the host machine. To understand how this info affect RiB, see [capabilities](./capabilities.md)

## syntax

```
rib env local info
```

## Example

```
rib:2.0.0@code# rib env local info
adb_support: true
dev_kvm_support: false
docker_engine_version: 20.10.11
gpu_support: false
host_os: Darwin
platform: x86_64
systemd_version: ''
rib:2.0.0@code#
```

## optional args

#### `--format`
Format output as JSON or YAML

