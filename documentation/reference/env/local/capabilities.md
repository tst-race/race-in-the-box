# Supported Capabilities of RiB

The purpose of this command is to understand what RiB capabilties are supported on the host machine.

## syntax

```
rib env local capabilities
```

## Example

```
rib:2.0.0@code# rib env local capabilities
Android:
  children:
    Android Bridge Mode:
      is_supported: true
    Android in Docker:
      is_supported: false
      reason: Android in docker requires dev kvm support
  is_supported: true
Local Deployments:
  children:
    GPU Deployments:
      is_supported: false
      reason: GPU deployments require drivers installed on a Linux host machine
  is_supported: true
rib:2.0.0@code#
```

## optional args

#### `--format`
Format output as JSON or YAML

