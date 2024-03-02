## Prerequisites

The below items are global prerequisites for utilizing RiB.

## Table of Contents

* [Dependencies](#dependencies)
* [Prerequisites](#prerequisites)
* [Further Reading](#further-reading)

## Dependencies

Dependencies/System Requirementås for the RiB system.

### Supported Operating Systems

* Mac
* Linux
* Windows (with Subsystem for Linux)

### Applications/Packages

* docker

## Prerequisites

### GitHub Access Token

* Users must provide an access token to pull images or kits from private GitHub repositories
    * See [`rib github config` reference docs](../reference/github/config.md) for details about creating the access token

### Docker (And GitHub Container Registry)

* Users must log into the GitHub Container Registy

```
localhost$ docker login ghcr.io -u {GITHUB_USERNAME}
>> Password: {GITHUB_TOKEN}
```

### Android Bridged Mode
* Android emulators and devices are supported in bridge mode. The following requirements must be met for the emulator/device:
    * API 29 (no other API level is currently supported)
    * 6GB of storage minimum
    * [ADB](https://developer.android.com/studio/command-line/adb) must be installed on the host machine

## Further Reading
At this point you should have the prequisites for RiB! To continue learning about the system read [How To Start RiB](./HOWTO-Start-RiB.md)