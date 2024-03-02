## HOWTO-Start-RiB

This document will detail how to start RiB with the correct directories and file structure, how to initialize all necessary state, and how to verify everything is properly ready to begin using RiB functionality.

## Steps To Start/Initialize RiB

- [HOWTO-Start-RiB](#howto-start-rib)
- [Steps To Start/Initialize RiB](#steps-to-startinitialize-rib)
  - [Download RiB](#download-rib)
  - [Start RiB](#start-rib)
  - [Initialize RiB State](#initialize-rib-state)
  - [Login to Docker](#login-to-docker)
  - [Use RIB UI](#use-rib-ui)
  - [Further Reading](#further-reading)

### Download RiB

The latest version of RiB can be found [here](https://github.com/tst-race/race-in-the-box)).

For a specific/stable version of rib, please choose the tag that corresponds with the version you plan on using. Tags can be found [here](https://github.com/tst-race/race-in-the-box/tags).

Clone this repository on the machine you plan on running RiB on and navigate to the root directory of the project.

### Start RiB

Use the Provided RiB Entrypoint Shell Script (located [here](../../entrypoints/)). rib_x.y.z.sh represents the version of rib that you want to use. Please update accordingly.

***Note*** Please use full/absolute paths for all supplied files/directories below

**{CODE_DIR}** is a required argument. You need to pass it a file path to the location of your plugin code and other necessary files. This will allow RiB to build and mount you plugin for use in RACE nodes, among other features.

**{SSH_KEYFILE}** is the location on your local machine of the private .ssh key that will be used to authenticate and SSH to AWS EC2 instances. If you do not mount an SSH_KEYFILE, you will not be able to use AWS deployments.

```
localhost$ cd entrypoints
localhost$ sh rib_x.y.z.sh --code={CODE_DIR} --ssh={SSH_KEYFILE}
rib:x.y.z@code# rib --help
Usage: rib [OPTIONS] COMMAND [ARGS]...

  RiB entrypoint command

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
...
```

### Initialize RiB State

Initializing state should be a one-time item for RiB. This information will be stored on your system for future RiB uses and help automate tasks.

```
rib:x.y.z@code# rib config init
What default detail level should be used for status/info reports (0=least detailed, 5=most detailed)? [0]: {DETAIL_LEVEL}
What default logging verbosity should be used (0=least verbose, 5=most verbose)? [0]: {VERBOSITY_LEVEL}
Initalized RiB Config
```

### Login to Docker

Logging into docker will allow for the local deployment to access images stored in private registries. This step will be removed in the future.

```
rib:x.y.z@code# rib docker login
>> Login Succeeded
>> Log Into Docker Container Successful
```

### Use RIB UI
The following is optional and not fully supported as of RiB 2.2.0

Refer to the [UI Docs](HOWTO-RIBUI.md) for details

### Further Reading
At this point RiB should be up and ready! To continue learning about how to use RiB please continue on to [the How Tos](../how-to)

The way to read the How Tos is to start with one of the "Test" documents:
- [manual deployment test](../how-to/manual-deployment-test.md)
- [automated deployment test](../how-to/automated-deployment-test.md)
- [automated network manager deployment test](../how-to/automated-network-manager-integration-test.md)
- [automated comms channel deployment test](../how-to/automated-ta2-integration-test.md)

The most basic one is [manual deployment test](../how-to/manual-deployment-test.md).

All of these "Test" documents have the same basic structure:
1. [deployment setup (different configurations are documented here)](../how-to/deployment-setup)
2. test steps (sending messages of some kind)
3. [verification (different methods are documented here)](../how-to/test-verification)
4. deployment teardown 