# Create AWS Topology By Node Resource Requirements

Creates an AWS node-instance topology from a fixed count of RACE nodes and
calculates the required number of host instances based on CPU/GPU/RAM resource
requirements of the RACE nodes.

## syntax

```
rib aws topology by-node-resource-requirements <args>
```

## example

```
1) rib:x.y.z@code# rib aws topology by-node-resource-requirements \
    --linux-x86_64-client-count=10 \
    --linux-x86_64-server-count=5 \
    --colocate
AWS Node Instance Topology:
	android arm64 instances:
	android x86_64 instances:
	linux GPU-enabled arm64 instances:
	linux GPU-enabled x86_64 instances:
	linux arm64 instances:
	linux x86_64 instances:
		Instance #1:
			EC2 instance type: t3a.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 2
			Linux Servers: 5
			RAM utilization: 28672.0/32768.0 (87.5%)
			CPU utilization: 7.0/8.0 (87.5%)
		Instance #2:
			EC2 instance type: t3a.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 7
			Linux Servers: 0
			RAM utilization: 28672.0/32768.0 (87.5%)
			CPU utilization: 7.0/8.0 (87.5%)
		Instance #3:
			EC2 instance type: t3a.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 1
			Linux Servers: 0
			RAM utilization: 4096.0/32768.0 (12.5%)
			CPU utilization: 1.0/8.0 (12.5%)
```

## required args

### node counts

At least one of the following node count parameters must be provided.

#### `--linux-x86_64-client-count INTEGER`

The number of Linux x86_64 client RACE nodes.

#### `--linux-x86_64-server-count INTEGER`

The number of Linux x86_64 server RACE nodes.

#### `--linux-gpu-x86_64-client-count INTEGER`

The number of Linux x86_64 client RACE nodes with GPU support.

#### `--linux-gpu-x86_64-server-count INTEGER`

The number of Linux x86_64 server RACE nodes with GPU support.

#### `--android-x86_64-client-count INTEGER`

The number of Android x86_64 client RACE nodes.

#### `--linux-arm64-client-count INTEGER`

The number of Linux arm64 client RACE nodes.

#### `--linux-arm64-server-count INTEGER`

The number of Linux arm64 server RACE nodes.

#### `--linux-gpu-arm64-client-count INTEGER`

The number of Linux arm64 client RACE nodes with GPU support.

#### `--linux-gpu-arm64-server-count INTEGER`

The number of Linux arm64 server RACE nodes with GPU support.

#### `--android-arm64-client-count INTEGER`

The number of Android arm64 client RACE nodes.

## optional args

#### `--colocate-across-instances`, `--colocate`

Allow nodes of different platforms and types to reside on the same instances. By
default, each instance will be designated as hosting only nodes of a particular
platform (Android vs Linux), GPU capability (with vs without GPU support), and
node type (client vs server).

#### `--format [json|yaml]`

If specified, the raw output format in which the AWS node-instance topology is
printed to the console.

#### `--out TEXT`

Location of file to which to write the AWS node-instance topology as a JSON
document.

### resource constraints

***NOTE***: RiB will not place any hard RAM or CPU limits on the RACE node
containers.  These resource requirements are only used to calculate the optimal
number of EC2 instance hosts to run the specified number of RACE nodes.

#### `--ram-per-android-client INTEGER`

Amount of RAM (in MB) used by each Android client.

#### `--ram-per-linux-client INTEGER`

Amount of RAM (in MB) used by each Linux client.

#### `--ram-per-linux-server INTEGER`

Amount of RAM (in MB) used by each Linux server.

#### `--ram-overcommit FLOAT`

Fraction of a node's RAM requirement to be shared with other nodes on the same
host. If the RAM per node is a peak usage rather than the nominal usage, setting
a RAM overcommit fraction may result in more nodes being assigned to a host.

For example, using a RAM overcommit fraction of 0.1 and 4096 MB of RAM per node,
each node will be allocated a guaranteed 3686 MB of RAM and 410 MB on each
instance host will be available for nodes for peak usage.

#### `--cpus-per-android-client FLOAT`

Fractional CPUs used by each Android client.

#### `--cpus-per-linux-client FLOAT`

Fractional CPUs used by each Linux client.

#### `--cpus-per-Linux-server FLOAT`

Fractional CPUs used by each Linux server.

#### `--cpu-overcommit FLOAT`

Fraction of a node's CPU requirement to be shared with other nodes on the same
host. If the CPUs per node is a peak usage rather than the nominal usage,
setting a CPU overcommit fraction may result in more nodes being assigned to a
host.

For example, using a CPU overcommit fraction of 0.2 and 1 CPU per node, each
node will be allocated a guaranteed 0.8 CPUs and 0.2 CPUs on each instance host
will be available for nodes for peak usage.

#### `--gpus-per-android-client FLOAT`

Fractional GPUs used by each Android client.

#### `--gpus-per-linux-client FLOAT`

Fractional GPUs used by each Linux client.

#### `--gpus-per-Linux-server FLOAT`

Fractional GPUs used by each Linux server.

#### `--gpu-overcommit FLOAT`

Fraction of a node's GPU requirement to be shared with other nodes on the same
host. If the GPUs per node is a peak usage rather than the nominal usage,
setting a GPU overcommit fraction may result in more nodes being assigned to a
host.

For example, using a GPU overcommit fraction of 0.2 and 1 GPU per node, each
node will be allocated a guaranteed 0.8 GPUs and 0.2 GPUs on each instance host
will be available for nodes for peak usage.

### instance types

#### `--linux-x86_64-instance-type TEXT`

The EC2 instance type used for hosting x86_64 Linux RACE nodes.

#### `--linux-gpu-x86_64-instance-type TEXT`

The EC2 instance type used for hosting x86_64 Linux RACE nodes with GPU support.

#### `--android-x86_64-instance-type TEXT`

The EC2 instance type used for hosting x86_64 Android RACE nodes.

#### `--linux-arm64-instance-type TEXT`

The EC2 instance type used for hosting arm64 Linux RACE nodes.

#### `--linux-gpu-arm64-instance-type TEXT`

The EC2 instance type used for hosting arm64 Linux RACE nodes with GPU support.

#### `--android-arm64-instance-type TEXT`

The EC2 instance type used for hosting arm64 Android RACE nodes.