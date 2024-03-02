# Create AWS Topology By Instance Count

Creates an AWS node-instance topology from a fixed count of RACE nodes evenly
distributed across a fixed count of host instances.

## syntax

```
rib aws topology by-instance-count <args>
```

## example

```
1) rib:x.y.z@code# rib aws topology by-instance-count \
    --linux-x86_64-client-count=10 \
    --linux-x86_64-server-count=5 \
    --linux-x86_64-instance-count=3
AWS Node Instance Topology:
	android arm64 instances:
	android x86_64 instances:
	linux GPU-enabled arm64 instances:
	linux GPU-enabled x86_64 instances:
	linux arm64 instances:
	linux x86_64 instances:
		Instance #1:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 5
			Linux Servers: 0
		Instance #2:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 5
			Linux Servers: 0
		Instance #3:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 0
			Linux Servers: 5
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

### instance counts

At least one of the following instance count parameters must be provided, and at
least one suitable host instance must be provided for each of the nodes
specified.

#### `--linux-x86_64-instance-count INTEGER`

The number of x86_64 EC2 instances suitable for hosting Linux RACE nodes.

#### `--linux-gpu-x86_64-instance-count INTEGER`

The number of GPU-capable x86_64 EC2 instances suitable for hosting Linux RACE
nodes with GPU support.

#### `--android-x86_64-instance-count INTEGER`

The number of x86_64 metal EC2 instances suitable for hosting Android RACE
nodes.

#### `--linux-arm64-instance-count INTEGER`

The number of arm64 EC2 instances suitable for hosting Linux RACE nodes.

#### `--linux-gpu-arm64-instance-count INTEGER`

The number of GPU-capable arm64 EC2 instances suitable for hosting Linux RACE
nodes with GPU support.

#### `--android-arm64-instance-count INTEGER`

The number of arm64 metal EC2 instances suitable for hosting Android RACE
nodes.

## optional args

#### `--colocate-clients-and-servers`, `--colocate`

Allow client and server nodes to reside on the same instances. By default,
each instance will be designated as hosting either clients or servers.

#### `--format [json|yaml]`

If specified, the raw output format in which the AWS node-instance topology is
printed to the console.

#### `--out TEXT`

Location of file to which to write the AWS node-instance topology as a JSON
document.
