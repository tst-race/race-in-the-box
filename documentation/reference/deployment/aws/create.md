# Create AWS Deployment

A **deployment** consists of:
- Plugins
    - artifacts (staged in
      `~/.race/rib/deployments/aws/<deployment_name>/plugins/dist/` then
        uploaded to artifact manager plugin services)
    - supplemental files (config generation scripts, external services scripts,
      etc.)
    - configs
- Information about RACE nodes
    - How many Linux servers, Linux clients, and Android clients
    - What docker images to use
- Generated docker-compose project files

Creating an AWS deployment gathers/creates the required files and places them in
in a new deployment directory `~/.race/rib/deployments/aws/<deployment_name>/`.

The specified RACE nodes are distributed across all the EC2 instances in the
host AWS environment, according to their type and capabilities (e.g., if Linux
nodes have GPU support). If the specified host does not contain an appropriate
number of EC2 instances for the RACE nodes specified in the deployment, the
create command will fail. The implicitly generated topology used for
distribution is the same as that created by the
`rib aws topology by-instance-count` command. If a node-instance topology JSON
file is specified (i.e., one resulting from a `rib aws topology` command), the
nodes will be distributed according to that topology. If the specified topology
does not include enough RACE nodes to fit the number of nodes in the deployment
or if the host AWS environment does not contain enough host instances to satisfy
the topology, the create command will fail.

## Syntax

```sh
rib deployment aws create <args>
```

## Example

Minimum required arguments

```
rib deployment aws create \
    --name=example-aws-deployment \
    --aws-env-name=example-aws-env \
    --linux-client-count=4 \
    --linux-server-count=8 \
    --colocate-clients-and-servers
```

## Arguments

### Required

`--name TEXT`

The name of the deployment. This is used for the directory name and is required
for other operations on the deployment.

`--aws-env-name TEXT`

The name of the host AWS environment. The AWS environment must already exist,
but does not have to be running when creating a deployment for it.

#### Node Options

> At least one node is required to create the deployment. The create command
> will fail if no node counts are specified.

`--android-client-count INTEGER`

*Default: 0*

The number of Android client nodes. The host AWS environment must contain at
least one Android EC2 instance or the create command will fail.

`--linux-client-count INTEGER`

*Default: 0*

The total number of Linux client nodes. The host AWS environment must contain
at least one Linux EC2 instance or the create command will fail. If colocation
is not enabled and the deployment also contains Linux server nodes, the host
AWS environment must contain at least two Linux EC2 instances or the create
command will fail.

`--linux-server-count INTEGER`

*Default: 0*

The total number of Linux server nodes. The host AWS environment must contain
at least one Linux EC2 instance or the create command will fail. If colocation
is not enabled and the deployment also contains Linux client nodes, the host
AWS environment must contain at least two Linux EC2 instances or the create
command will fail.

`--registry-client-count INTEGER`

*Default: 0*

The total number of Linux registry nodes. Registry nodes are similar to clients,
so all constraints about Linux EC2 instances in the host AWS environment related
to clients also holds true for registry nodes.

### Optional

`--force`

By default the create command will fail if there is already an AWS
deployment/directory of the same name in `~/.race/rib/deployments/aws/`. Setting
this switch will overwrite the existing deployment.

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
    --default-race-images-tag def-tag
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

#### Topology Options

`--colocate-clients-and-servers, --colocate`

If using the implicitly generated topology, enables colocation of clients and
servers on the same host instance. By default, an EC2 instance will only host
either client or server RACE nodes. Settings this switch will allow for an EC2
instance to host both client and server RACE nodes. This is required if only one
EC2 instance exists in order to create a deployment with both clients and
servers.

`--topology TEXT`

Path to a node-instance topology JSON file to be used for distributing
RACE nodes across the instances in the host AWS environment.

#### Range-Config Definition Options

`--range TEXT`

*Default: none*

Location of a range config file to use.

When no range config file is specified, RiB creates one in order to use with
config generation scripts. Otherwise the specified range config file is used.

This option is mutually exclusive with any node count definition options.

#### Node Count Definition Options

`--android-client-arch [arm64|x86_64]`

The architecture of all managed Android client containers. At least one Android
EC2 instance of the specified architecture must exist in the host AWS
environment.

`--android-client-uninstalled-count INTEGER`

*Default: 0*

Number of Android client nodes that will not have the RACE app preinstalled
when they start. Must be less than the total number of Android client nodes.

`--android-client-bridge-count INTEGER`

*Default: 0*

Number of Android client nodes that will be bridged into the RACE network. These
nodes will not have a docker container and will not run in the host AWS
environment.

`--linux-client-arch [arm64|x86_64]`

The architecture of all Linux client containers (with or without GPU support).
At least one Linux EC2 instance of the specified architecture must exist in the
host AWS environment.

`--linux-client-uninstalled-count INTEGER`

*Default: 0*

Number of Linux client nodes that will not have the RACE app preinstalled
when they start. Must be less than the total number of Linux client nodes.

`--linux-server-arch [arm64|x86_64]`

The architecture of all Linux server containers (with or without GPU support).
At least one Linux EC2 instance of the specified architecture must exist in the
host AWS environment.

`--linux-server-uninstalled-count INTEGER`

*Default: 0*

Number of Linux server nodes that will not have the RACE app preinstalled
when they start. Must be less than the total number of Linux server nodes.

`--linux-gpu-client-count INTEGER`

*Default: 0*

Number of Linux client nodes that will have GPU-support. Must be less than or
equal to the total number of Linux client nodes. The host AWS environment must
contain at least one GPU Linux EC2 instance or the create command will fail. If
colocation is not enabled and the deployment also contains GPU-enabled Linux
server nodes, the host AWS environment must contain at least two GPU Linux EC2
instances or the create command will fail.

`--linux-gpu-server-count INTEGER`

*Default: 0*

Number of Linux server nodes that will have GPU-support. Must be less than or
equal to the total number of Linux server nodes. The host AWS environment must
contain at least one GPU Linux EC2 instance or the create command will fail. If
colocation is not enabled and the deployment also contains GPU-enabled Linux
client nodes, the host AWS environment must contain at least two GPU Linux EC2
instances or the create command will fail.
