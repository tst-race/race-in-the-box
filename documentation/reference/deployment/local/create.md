# Create Local Deployment

A **deployment** consists of:
 - Plugins
    - artifacts
    - supplemental files (config generation scripts, external services scripts,
      etc.)
    - configs
 - Information about RACE Nodes
    - How many linux servers, linux clients, android clients
    - What docker images to use
- Generated docker-compose project file

Creating a local deployment gathers/creates the required files and places them
in a new deployment directory `~/.race/rib/deployments/local/<deployment_name>/`

## Syntax

```sh
rib deployment local create <args>
```

## Example

Minimum required arguments

```sh
rib deployment local create \
    --name example-local-deployment \
    --linux-client-count 3 \
    --linux-server-count 3
```

## Arguments

### Required

`--name TEXT`

The name of the deployment. This is used for the directory name and is required
for future operations on the deployment.

> At least one of the following node types must be specified, unless using a
> range config file. Depending on the network manager plugin being used, a
> minimum number of clients or servers may also be required.

`--linux-server-count INTEGER`

*Default: 0*

The number of Linux servers to include (used in the docker-compose)

`--linux-client-count INTEGER`

*Default: 0*

The number of Linux clients to include (used in the docker-compose) 

`--android-client-count INTEGER`

*Default: 0*

The number of Android clients to include (used in the docker-compose) 

The Android clients will come after the Linux clients when assigning
numerically-ordered personas. That is, given:

```sh
rib deployment local create \
    --linux-client-count 1 \
    --android-client-count 1
```

`race-client-00001` will be a Linux client and `race-client-00002` will be an
Android client.

### Optional

`--force`

By default the create command will fail if there is already a
deployment/directory of the same name in `~/.race/rib/deployments/local/`. Force
can be used to overwrite the existing deployment

`--disable-elasticsearch-volume-mounts`

Disabling elasticsearch volume mounts disables perstistance for OpenTracing.
This option should only be used if your local machine does not allow
elasticsearch volume mounts (usually due to permissions issues)

`--enabled-gpu`

Enable GPU support in RACE nodes

`--tmpfs INTEGER`

If set, will create a tmpfs mount at `/tmpfs` of specified size in bytes

`--disable-open-tracing`

Disable Open Tracing (Running without open tracing will not permit message
verification with RiB)

#### Application Configuration Options

`--disabled-channel TEXT`

Name of a comms channel to be initially disabled on first start on each RACE
node

`--fetch-plugins-on-start`

Enable fetching of plugins from artifact managers on application start. Plugins
are supplied to artifact managers from
`~/.race/rib/deployments/local/<deployment_name>/plugins/dist/`

`--no-config-gen`

Prevent default config generation from running after the deployment is created

`--disable-config-encryption`

Disable encryption of runtime configs on disk. When disabled, configs will be
stored in plaintext on RACE nodes.

`--race-log-level [debug|info|warning|error]`

*Default: debug*

Set the logging level for the RACE app on each node

#### Kit Options

`--cache [never|always|auto]`

*Default: auto* 

Whether to use locally-cached kits or to re-fetch the kits from their specified
sources.

Options:
* `never`: always re-download the kit every time this command is run
* `always`: use cached copy of the kit if it exists, else download it into the
  cache
* `auto`: re-downloads if using a branch source, else uses the cached copy if
  it exists

The cache is located at `~/.race/rib/plugins-cache/`.

`--race-core TEXT`

*Default: user-configurable tagged release*

Source for the RACE core kits. See the [kit-source](../../../general/kit-source.md)
guide for details about supported source formats.

If this argument is not specified, the default as configured by the
[rib github config](../../github/config.md) command will be used.

`--network-manager-kit TEXT`

*Default: core=plugin-network-manager-twosix-cpp*

Source for the network manager plugin kit. See the [kit-source](../../../general/kit-source.md)
guide for details about supported source formats.

If this argument is not specified, the stub network manager kit from the
corresponding RACE core will be used.

`--comms-channel TEXT`

*Default: twoSixDirectCpp, twoSixIndirectCpp, twoSixIndirectBootstrapCpp*

Names of the comms channels to enable in the deployment. This option can be
used multiple times to specify any number of channels. If it is specified, none
of the default channel names are used.

Each channel must have a corresponding comms kit that provides the channel. If
a channel is specified but no comms kit provides it, the deployment will not be
created.

`--comms-kit TEXT`

*Default: core=plugin-comms-twosix-cpp*

Sources for the comms plugin kits. See the [kit-source](../../../general/kit-source.md)
guide for details about supported source formats.

This option can be used multiple times to specify any number of kits. If it is
specified, the default kit will not be used.

The specified kits must provide all channels required for the deployment. If a
channel is specified but no comms kit provides it, the deployment will not be
created.

`--artifact-manager-kit TEXT`

*Default: core=plugin-artifact-manager-twosix-cpp-local, core=plugin-artifact-manager-twosix-cpp*

Sources for the artifact manager plugin kits. See the
[kit-source](../../../general/kit-source.md) guide for details about supported
source formats.

This option can be used multiple times to specify any number of kits. If it is
specified, the default kits will not be used.

`--android-app TEXT`

*Default: core=raceclient-android*

Source for the Android client app kit. See the
[kit-source](../../../general/kit-source.md) guide for details about supported
source formats.

`--linux-app TEXT`

*Default: core=racetestapp-linux*

Source for the Linux app kit. See the
[kit-source](../../../general/kit-source.md) guide for details about supported
source formats.

`--registry-app TEXT`

*Default: none*

Source for the registry app kit. See the
[kit-source](../../../general/kit-source.md) guide for details about supported
source formats.

`--node-daemon TEXT`

*Default: core=race-node-daemon*

Source for the node daemon app kit. See the
[kit-source](../../../general/kit-source.md) guide for details about supported
source formats.

#### Docker Image Options

For all Docker image options, the default image org, repo, and tag as configured
by the [rib github config](../../github/config.md) command affect the default
image values as well as the fully expanded image name when only a tag is
provided.

For example, given that `rib github config` has been run as:

```sh
rib github config \
    --default-race-images-org def-org \
    --default-race-images-repo def-repo \
    --default-race-images-tag def-tag \
```

An image option value of `:my-tag` would be expanded to
`ghcr.io/def-org/def-repo/race-runtime-linux:other-tag`, while a value of
`race-runtime-linux:other-tag` is unaltered.

`--android-client-image TEXT`

*Default: user-configurable tag of race-runtime-android-x86_64*

Docker image to use for managed Android client nodes.

`--linux-client-image TEXT`

*Default: user-configurable tag of race-runtime-linux*

Docker image to use for Linux client nodes.

`--linux-server-image TEXT`

*Default: user-configurable tag of race-runtime-linux*

Docker image to use for Linux server nodes.


#### Range-Config Definition Options

`--range TEXT`

*Default: none*

Location of a range config file to use.

When no range config file is specified, RiB creates one in order to use with
config generation scripts. Otherwise the specified range config file is used.

This option is mutually exclusive with any node count definition options.

#### Node Count Definition Options

These options are mutually exclusive with the `--range` option.

`--android-client-uninstalled-count INTEGER`

*Default: 0*

Number of Android clients to include without the RACE app preinstalled.

These clients will be the last of the Android clients. For example, given:

```sh
rib deployment local create \
    --linux-client-count 2 \
    --android-client-count 2 \
    --android-client-uninstalled-count 1
```

`race-client-00003` will be a genesis Android client and `race-client-00004`
will be a non-genesis, uninstalled Android client.

`--android-client-bridge-count INTEGER`

*Default: 0*

Number of Android clients that will be bridged into the RACE network. See the
[android-bridged](../../../how-to/deployment-setup/android-bridged.md) guide
for additional information about bridged Android clients.

These clients will be the last of the Android clients. For example, given:

```sh
rib deployment local create \
    --linux-client-count 2 \
    --android-client-count 2 \
    --android-client-bridge-count 1
```

`race-client-00003` will be a managed Android client and `race-client-00004`
will be a bridged Android client.

`--linux-client-uninstalled-count INTEGER`

*Default: 0*

Number of Linux clients to include without the RACE app preinstalled.

These clients will be the last of the Linux clients. For example, given:

```sh
rib deployment local create \
    --linux-client-count 2 \
    --linux-client-uninstalled-count 1
```

`race-client-00001` will be a genesis Linux client and `race-client-00002`
will be a non-genesis, uninstalled Linux client.

`--registry-client-count INTEGER`

*Default: 0*

The number of Registry clients to include (used in the docker-compose)
