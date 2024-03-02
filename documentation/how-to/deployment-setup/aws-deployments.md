# Setting Up an AWS Deployment

This document will detail how to use RiB to set up a RACE deployment in an AWS
environment.

An AWS **environment** consists of:
- Ansible playbooks
- CloudFormation templates

When provisioned, the environment is responsible for:
- Creating AWS resources
- Configuring EC2 instances to run docker

When unprovisioned, the environment is responsible for:
- Deleting AWS resources

An AWS **deployment** consists of:
- Plugins
    - artifacts (uploaded to artifact manager plugin services)
    - supplemental files (config generation scripts, external services scripts,
      etc.)
    - configs
- Information about RACE nodes
    - How many Linux servers, Linux clients, and Android clients
    - What docker images to use

When stood up, the deployment is responsible for:
- Downloading plugins
- Generating plugin configuration
- Pulling docker images
- Starting all containers (services, RACE nodes)

When torn down, the deployment is responsible for:
- Stopping all containers (services, RACE nodes)
- Removing configs and scripts
- Optionally, purging docker images

## Steps

* [Prerequisites](#prerequisites)
	* [RiB Configuration](#rib-configuration)
	* [Calculating AWS Resource Requirements](#calculating-aws-resource-requirements)
	* [Determine Plugin Revisions](#determine-plugin-revisions)
		* [1 network manager plugin](#1-network-manager-plugin)
		* [1 or more comms channels](#1-or-more-comms-channels)
		* [1 or more artifact manager plugins](#1-or-more-artifact-manager-plugins)
	* [Important Note on Docker Images](#important-note-on-docker-images)
* [Create an AWS Environment](#create-an-aws-environment)
* [Create an AWS Deployment](#create-an-aws-deployment)
* [Provision the AWS Environment](#provision-the-aws-environment)
* [Verify State of the AWS Environment](#verify-state-of-the-aws-environment)
	* [Environment Status](#environment-status)
	* [Environment Runtime Info](#environment-runtime-info)
	* [SSH Connectivity](#ssh-connectivity)
* [Stand Up the AWS Deployment](#stand-up-the-aws-deployment)
* [Verify State of the AWS Deployment](#verify-state-of-the-aws-deployment)
	* [Deployment Status](#deployment-status)
	* [Bastion SSH Connectivity](#bastion-ssh-connectivity)
* [Run Tests Against the AWS Deployment](#run-tests-against-the-aws-deployment)
* [Backup Logs From the AWS Deployment](#backup-logs-from-the-aws-deployment)
* [Tear Down the AWS Deployment](#tear-down-the-aws-deployment)
* [Unprovision the AWS Environment](#unprovision-the-aws-environment)

## Prerequisites

### RiB Configuration

Ensure that RiB has been configured to use your AWS account and all
[AWS prerequisites](../../general/aws-prerequisites.md) are met.

### Calculating AWS Resource Requirements

Follow the [Calculating AWS Resource Requirements](calculating-aws-resource-requirements.md)
guide to determine the appropriate number (and type) of EC2 instances to create
in the host AWS environment.

### Determine Plugin Revisions

An AWS deployment must have:

#### 1 network manager plugin

See the [kit source](../../general/kit-source.md) guide for additional details
about specifying a kit source for the network manager plugin.

#### 1 or more comms channels

Most deployments require at least one direct channel and one indirect channel.
This is because client-to-server and server-to-client connections must use
indirect channel. Direct channels *usually* have higher bandwith and are used
for server-to-server connections. You can find more information about Comms
channels on the
[Confluence Wiki](https://wiki.race.twosixlabs.com/display/RACE2/Channel+Surveys)

See the [kit source](../../general/kit-source.md) guide for additional details
about specifying a kit source for comms channels.

#### 1 or more artifact manager plugins

The artifact manager plugins are used if `--fetch-plugins-on-start` is enabled
or when bootstrapping a new node.

See the [kit source](../../general/kit-source.md) guide for additional details
about specifying a kit source for artifact manager plugins.

### Important Note on Docker Images

Unlike a local deployment, which volume-mounts the race artifacts into the
RACE node containers, the RACE node images used in an AWS deployment must
contain the race artifacts. 
**Key Point:** *use exemplar images, NOT runnable images*

Plugin artifacts can be pulled at deployment 
start using `--fetch-plugins-on-start` in the deployment create command.

After/Around test events, Two Six will also generate Complete images
(e.g. race-linux-client-complete) that have all performer plugins installed.
These are the images that will be tested on the range and will also be available
for testing with AWS environments.

## Create an AWS Environment

Create the AWS environment using the desired EC2 instance counts. The SSH key
name must match the key previously set up in AWS and used when starting RiB.

```
1) rib:x.y.z@code# rib env aws create \
    --name=example-aws-env \
    --ssh-key-name=race-develop_name \
    --android-x86_64-instance-count=1 \
    --linux-gpu-x86_64-instance-count=1 \
    --linux-x86_64-instance-count=1
Creating AWS Environment: example-aws-env
	1 c5.metal EC2 instances for RACE nodes
	1 p3.2xlarge EC2 instances for RACE nodes
	1 t3a.2xlarge EC2 instances for RACE nodes
	1 t3a.2xlarge EC2 instance as the cluster manager
	1 t3a.2xlarge EC2 instance as the external service host
Do you want to proceed? [y/N]: y
Created AWS Environment: example-aws-env
```

*See the [`rib env aws create`](../../reference/env/aws/create.md) reference for
additional details.*

## Create an AWS Deployment

Create the AWS deployment, specifying the name of the previously created AWS
environment as the desired host environment.

***NOTE*** It is possible to create multiple AWS deployments against the same
host AWS environment with different network sizes, RACE node images, plugins,
or configs. Though only one deployment may be active on the host environment
at any given time.

```
rib deployment aws create \
    --name=example-aws-deployment \
    --aws-env-name=example-aws-env \
    --android-client-count=2 \
    --linux-client-count=4 \
    --linux-server-count=8 \
    --linux-gpu-server-count=4 \
    --colocate-clients-and-servers \
    --android-client-image=ghcr.io/tst-race/race-images/race-runtime-android-x86_64:x.y.z \
    --linux-client-image=ghcr.io/tst-race/race-images/race-runtime-linux:x.y.z \
    --linux-server-image=ghcr.io/tst-race/race-images/race-runtime-linux:x.y.z \
    --race=x.y.z \
	--network-manager-kit=core=plugin-network-manager-twosix-cpp \
    --comms-channel=twoSixDirectCpp \
    --comms-channel=twoSixIndirectCpp \
	--comms-kit=core=plugin-comms-twosix-cpp \
    --artifact-manager-kit=core=plugin-artifact-manager-twosix-cpp \
    --fetch-plugins-on-start
```

*See the [`rib deployment aws create`](../../reference/deployment/aws/create.md)
reference for additional details.*

## Provision the AWS Environment

Provision the AWS environment to create all AWS resources and prepare the EC2
instances to host the deployment.

***NOTE*** Once provisioned, the AWS environment will begin accruing AWS billing
charges. Be mindful of how costly the environment may be and how long it is left
running.

```
1) rib:x.y.z@code# rib env aws provision --name=example-aws-env
Provisioning AWS Environment: example-aws-env
Provisioned AWS Environment: example-aws-env
```

*See the [`rib env aws provision`](../../reference/env/aws/provision.md)
reference for additional details.*

## Verify State of the AWS Environment

### Environment Status

Once the AWS environment has been provisioned, verify that everything has been
started correctly by checking the status of the environment.

```
1) rib:x.y.z@code# rib env aws status --name=example-aws-env -ddd
AWS Environment example-aws-env is ready
	cloud formation: ready
		race-example-aws-env-android-x86-64-node-host: ready
		race-example-aws-env-cluster-manager: ready
		race-example-aws-env-efs: ready
		race-example-aws-env-linux-gpu-x86-64-node-host: ready
		race-example-aws-env-linux-x86-64-node-host: ready
		race-example-aws-env-network: ready
		race-example-aws-env-service-host: ready
	ec2 instance: ready
		android-x86-64-node-host: ready
			ec2-54-242-56-152.compute-1.amazonaws.com: ready
		cluster-manager: ready
			ec2-3-87-139-229.compute-1.amazonaws.com: ready
		linux-gpu-x86-64-node-host: ready
			ec2-54-196-99-132.compute-1.amazonaws.com: ready
		linux-x86-64-node-host: ready
			ec2-54-91-254-209.compute-1.amazonaws.com: ready
		service-host: ready
			ec2-54-144-32-96.compute-1.amazonaws.com: ready
	efs: ready
		race-example-aws-env-DataFileSystem: ready
```

*See the [`rib env aws status`](../../reference/env/aws/status.md) reference for
additional details.*

If the AWS environment is not completely ready, try to re-provision the
environment by re-running the `rib env aws provision` command to correct the
issue. If the environment fails to fully provision to a ready status, please
reach out to Two Six for assistance.

### Environment Runtime Info

The IP addresses of all EC2 instances can be seen in the runtime info for the
environment.

```
1) rib:x.y.z@code# rib env aws runtime-info --name=example-aws-env
android-x86-64-node-host:
- containers: {}
  private_dns: ip-10-0-0-30.ec2.internal
  private_ip: 10.0.0.30
  public_dns: ec2-54-242-56-152.compute-1.amazonaws.com
  public_ip: 54.242.56.152
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: android-x86-64-node-host
    Creator: rib
    Name: race-example-aws-env-android-x86-64-node-host
    Stack: race-example-aws-env-android-x86-64-node-host
    race_cost_service: RiB AWS Env
cluster-manager:
- containers: {}
  private_dns: ip-10-0-0-198.ec2.internal
  private_ip: 10.0.0.198
  public_dns: ec2-3-87-139-229.compute-1.amazonaws.com
  public_ip: 3.87.139.229
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: cluster-manager
    Creator: rib
    Name: race-example-aws-env-cluster-manager
    Stack: race-example-aws-env-cluster-manager
    race_cost_service: RiB AWS Env
linux-gpu-x86-64-node-host:
- containers: {}
  private_dns: ip-10-0-0-126.ec2.internal
  private_ip: 10.0.0.126
  public_dns: ec2-54-196-99-132.compute-1.amazonaws.com
  public_ip: 54.196.99.132
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: linux-gpu-x86-64-node-host
    Creator: rib
    Name: race-example-aws-env-linux-gpu-x86-64-node-host
    Stack: race-example-aws-env-linux-gpu-x86-64-node-host
    race_cost_service: RiB AWS Env
linux-x86-64-node-host:
- containers: {}
  private_dns: ip-10-0-0-15.ec2.internal
  private_ip: 10.0.0.15
  public_dns: ec2-54-91-254-209.compute-1.amazonaws.com
  public_ip: 54.91.254.209
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: linux-x86-64-node-host
    Creator: rib
    Name: race-example-aws-env-linux-x86-64-node-host
    Stack: race-example-aws-env-linux-x86-64-node-host
    race_cost_service: RiB AWS Env
service-host:
- containers: {}
  private_dns: ip-10-0-0-186.ec2.internal
  private_ip: 10.0.0.186
  public_dns: ec2-54-144-32-96.compute-1.amazonaws.com
  public_ip: 54.144.32.96
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: service-host
    Creator: rib
    Name: race-example-aws-env-service-host
    Stack: race-example-aws-env-service-host
    race_cost_service: RiB AWS Env
```

*See the [`rib env aws runtime-info`](../../reference/env/aws/runtime-info.md)
reference for additional details.*

### SSH Connectivity

Using the IP addresses from the runtime info, you can SSH into the EC2 instances
using port 2222.

```
1) rib:x.y.z@code# ssh -i ~/.ssh/rib_private_key -p 2222 rib@i.j.k.l
```

## Stand Up the AWS Deployment

Once the AWS environment is ready, stand up the AWS deployment to upload
configs, and start the RACE node containers.

***NOTE*** This will take a while to run as it has to pull all the docker images
needed for the deployment.

```
1) rib:x.y.z@code# rib deployment aws up --name=example-aws-deployment
Standing Up AWS Deployment: example-aws-deployment
Verifying Precondition, expecting down
Verifying Postcondition, expecting up
Stood Up AWS Deployment: example-aws-deployment
```

*See the [`rib deployment aws up`](../../reference/deployment/aws/up.md)
reference for additional details.*

## Verify State of the AWS Deployment

### Deployment Status

Once the AWS deployment has been stood up, verify that everything has been
started correctly by checking the status of the deployment.

```
1) rib:x.y.z@code# rib deployment aws status --name=example-aws-deployment -ddd
Deployment example-aws-deployment apps are up
	race-client-00001: up
		app: installed
		daemon: started
	race-client-00002: up
		app: installed
		daemon: started
	race-client-00003: up
		app: installed
		daemon: started
	race-client-00004: up
		app: installed
		daemon: started
	race-client-00005: up
		app: installed
		daemon: started
	race-client-00006: up
		app: installed
		daemon: started
	race-server-00001: up
		app: installed
		daemon: started
	race-server-00002: up
		app: installed
		daemon: started
	race-server-00003: up
		app: installed
		daemon: started
	race-server-00004: up
		app: installed
		daemon: started
	race-server-00005: up
		app: installed
		daemon: started
	race-server-00006: up
		app: installed
		daemon: started
	race-server-00007: up
		app: installed
		daemon: started
	race-server-00008: up
		app: installed
		daemon: started
Deployment example-aws-deployment container status is all running
	android-x86-64-node-host: all running
		ec2-54-242-56-152.compute-1.amazonaws.com: all running
			race-client-00001: running
			race-client-00002: running
	cluster-manager: all running
		ec2-3-87-139-229.compute-1.amazonaws.com: all running
			elasticsearch: running
			jaeger-collector: running
			jaeger-query: running
			kibana: running
			rib-bastion: running
			rib-file-server: running
			rib-redis: running
	linux-gpu-x86-64-node-host: all running
		ec2-54-196-99-132.compute-1.amazonaws.com: all running
			race-server-00005: running
			race-server-00006: running
			race-server-00007: running
			race-server-00008: running
	linux-x86-64-node-host: all running
		ec2-54-91-254-209.compute-1.amazonaws.com: all running
			race-client-00003: running
			race-client-00004: running
			race-client-00005: running
			race-client-00006: running
			race-server-00001: running
			race-server-00002: running
			race-server-00003: running
			race-server-00004: running
Deployment example-aws-deployment services status is all running
	External Services: all running
		PluginArtifactManagerTwoSixCpp: running
		twoSixIndirectCpp: running
	RiB: all running
		ElasticSearch: running
		File Server: running
		Jaeger UI: running
		Kibana: running
		Redis: running
```

At this point, it is expected that:
* All RACE apps are up (app installed, daemon started)
* All containers are running
* All services are running

*See the [`rib deployment status`](../../reference/deployment/status.md)
reference for additional details.*

If the AWS deployment is not in a good state, try to re-stand up the deployment
by re-running the `rib deployment aws up` command to correct the issue. If the
deployment fails to fully stand up to a good state, please reach out to Two
Six for assistance.

### Bastion SSH Connectivity

Using the IP address of the cluster manager instance as obtained from the
host AWS environment runtime info, you can SSH into bastion and from there
SSH into all RACE nodes.

```
1) rib:x.y.z@code# ssh -i ~/.ssh/rib_private_key rib@i.j.k.l
rib@rib-bastion:~$ ssh race-client-00001
root@race-client-0001:~#
```

## Run Tests Against the AWS Deployment

The RACE deployment is now ready to be used for tests. Use
`rib-use aws <deployment_name>` to enable shortcut commands for interacting with
the deployment.

```
1) rib:x.y.z@code# rib-use aws example-aws-deployment
2) rib:x.y.z:aws:example-aws-deployment@code# rib deployment start
```

## Backup Logs From the AWS Deployment

You may use the `rib deployment aws logs` commands to backup or rotate log
files, but doing so will incur some additional cost for the egress of the log
files out of AWS to your local machine. Depending on the size of the logs, this
could be a substantial cost.

*See the [`rib deployment logs rotate`](../../reference/deployment/logs/rotate.md)
reference for additional details.*

## Tear Down the AWS Deployment

When all testing with the deployment is finished, tear down the AWS deployment
to stop all RACE node containers and all services. The docker images are left on
the EC2 instances, so subsequent deployment runs on the environment will be
faster to stand up.

```
1) rib:x.y.z@code# rib deployment aws down --name=example-aws-deployment
Tearing Down AWS Deployment: example-aws-deployment
Verifying Precondition, expecting up
Verifying Postcondition, expecting down
Tore Down AWS Deployment: example-aws-deployment
```

If disk space used by the RACE node docker images is a concern, you can delete
all data from the deployment by adding the `--purge` switch to the
`rib deployment aws down` command.

Verify that everything has been stopped correctly by checking the status of the
deployment.

```
1) rib:x.y.z@code# rib deployment aws status --name=example-aws-deployment -ddd
Deployment example-aws-deployment apps are down
	race-client-00001: down
		daemon: unknown
	race-client-00002: down
		daemon: unknown
	race-client-00003: down
		daemon: unknown
	race-client-00004: down
		daemon: unknown
	race-client-00005: down
		daemon: unknown
	race-client-00006: down
		daemon: unknown
	race-server-00001: down
		daemon: unknown
	race-server-00002: down
		daemon: unknown
	race-server-00003: down
		daemon: unknown
	race-server-00004: down
		daemon: unknown
	race-server-00005: down
		daemon: unknown
	race-server-00006: down
		daemon: unknown
	race-server-00007: down
		daemon: unknown
	race-server-00008: down
		daemon: unknown
Deployment example-aws-deployment container status is all down
	android-x86-64-node-host: all down
		ec2-54-242-56-152.compute-1.amazonaws.com: all down
			race-client-00001: exited
			race-client-00002: exited
	cluster-manager: all down
		ec2-18-232-116-78.compute-1.amazonaws.com: all down
			elasticsearch: exited
			jaeger-collector: exited
			jaeger-query: exited
			kibana: exited
			rib-bastion: exited
			rib-file-server: exited
			rib-redis: exited
	linux-gpu-x86-64-node-host: all down
		ec2-54-196-99-132.compute-1.amazonaws.com: all down
			race-server-00005: exited
			race-server-00006: exited
			race-server-00007: exited
			race-server-00008: exited
	linux-x86-64-node-host: all down
		ec2-54-91-254-209.compute-1.amazonaws.com: all down
			race-client-00003: exited
			race-client-00004: exited
			race-client-00005: exited
			race-client-00006: exited
			race-server-00001: exited
			race-server-00002: exited
			race-server-00003: exited
			race-server-00004: exited
Deployment example-aws-deployment services status is all down
	External Services: all down
		PluginArtifactManagerTwoSixCpp: not running
		twoSixIndirectCpp: not running
	RiB: all down
		ElasticSearch: not running
		File Server: not running
		Jaeger UI: not running
		Kibana: not running
		Redis: not running
```

If the AWS deployment has not been completely torn down, try to re-tear down the
deployment by re-running the `rib deployment aws down` command to correct the
issue.

***NOTE*** The AWS resources are still running in AWS and still accruing AWS
billing charges.

At this point, the deployment may be re-stood up or a different deployment may
be stood up on the same AWS environment.

*See the [`rib deployment aws down`](../../reference/deployment/aws/down.md)
reference for additional details.*

## Unprovision the AWS Environment

Once all use of the AWS environment is finished, make sure to unprovision the
AWS environment to avoid additional AWS billing charges.

```
1) rib:x.y.z@code# rib env aws unprovision --name=example-aws-env
Unprovisioning AWS Environment: example-aws-env
Unprovisioned AWS Environment: example-aws-env
```

Verify that the environment has been completely stopped by checking the status
of the environment as well as listing all active AWS environments.

```
1) rib:x.y.z@code# rib env aws status --name=example-aws-env -ddd
AWS Environment example-aws-env is not present
	cloud formation: not present
		race-example-aws-env-android-x86-64-node-host: not present
		race-example-aws-env-cluster-manager: not present
		race-example-aws-env-efs: not present
		race-example-aws-env-linux-gpu-x86-64-node-host: not present
		race-example-aws-env-linux-x86-64-node-host: not present
		race-example-aws-env-network: not present
		race-example-aws-env-service-host: not present
	ec2 instance: not present
		android-x86-64-node-host: not present
			i-0089839b8015e7c4d: not present
		cluster-manager: not present
			i-0d44c5b8db6a134a3: not present
		linux-gpu-x86-64-node-host: ready
			i-07d5c319223b2bfcb: not present
		linux-x86-64-node-host: not present
			i-0d5cdc17feea5fd34: not present
		service-host: not present
			i-0b6c769855e4ec9a0: not present
	efs: not present
		race-example-aws-env-DataFileSystem: not present
1) rib:x.y.z@code# rib env aws active
No Active AWS Environments Found
```

If the environment has not been completely destroyed, try to re-unprovision the
environment by re-running the `rib env aws unprovision` command. If the
environment still cannot be removed, you may need to manually delete the
CloudFormation stacks using the AWS management console.

Each environment will create 5-10 CloudFormation stacks depending on host
architecture whether any GPU or Android instances were part of the environment:

* `race-{AWS_ENV_NAME}-network`: Creates VPCs, subnets, internet gateways,
  security groups, etc
* `race-{AWS_ENV_NAME}-efs`: Creates /data EFS mount for shared
  data across all EC2 instances (and volume mounted into all containers)
* `race-{AWS_ENV_NAME}-cluster-manager`: Creates 1 EC2 instance for running
  Bastion, OpenTracing, and RiB-specific orchestration services
* `race-{AWS_ENV_NAME}-service-host`: Creates 1 EC2 instance for running comms
  channel and artifact manager plugin external services (e.g., whiteboards)
* `race-{AWS_ENV_NAME}-android-arm64-node-host`: Creates a fixed-size autoscale
  group of EC2 instances for running RACE Android arm64 client nodes (if
  specified)
* `race-{AWS_ENV_NAME}-android-x86-64-node-host`: Creates a fixed-size autoscale
  group of EC2 instances for running RACE Android x86_64 client nodes (if
  specified)
* `race-{AWS_ENV_NAME}-linux-gpu-arm64-node-host`: Creates a fixed-size
  autoscale group of EC2 instances for running RACE GPU-enabled Linux arm64
  nodes (if specified)
* `race-{AWS_ENV_NAME}-linux-gpu-x86-64-node-host`: Creates a fixed-size
  autoscale group of EC2 instances for running RACE GPU-enabled Linux x86_64
  nodes (if specified)
* `race-{AWS_ENV_NAME}-linux-arm64-node-host`: Creates a fixed-size autoscale
  group of EC2 instances for running RACE non-GPU Linux arm64 nodes (if
  specified)
* `race-{AWS_ENV_NAME}-linux-x86-64-node-host`: Creates a fixed-size autoscale
  group of EC2 instances for running RACE non-GPU Linux x86_64 nodes (if
  specified)

All AWS services are created from CloudFormation. If you need to manually stop
any AWS services externally from RiB; you can destroy these stacks. Once they
have been fully deleted, there should be no services running in AWS and no more
charges should be accrued.
