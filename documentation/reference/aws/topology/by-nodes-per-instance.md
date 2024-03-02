# Create AWS Topology By Nodes-per-Instance Constraints

Creates an AWS node-instance topology from given nodes-per-instance constraints
and either a fixed count of RACE nodes or a fixed count of host instances.

## syntax

```
rib aws topology by-nodes-per-instance <args>
```

## example

```
1) rib:x.y.z@code# rib aws topology by-nodes-per-instance \
    --linux-x86_64-clients-per-instance=5 \
    --linux-x86_64-servers-per-instance=5 \
    --linux-x86_64-client-count=12 \
    --linux-x86_64-server-count=6
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
			Linux Clients: 4
			Linux Servers: 0
		Instance #2:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 4
			Linux Servers: 0
		Instance #3:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 4
			Linux Servers: 0
		Instance #4:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 0
			Linux Servers: 3
		Instance #5:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 0
			Linux Servers: 3

1) rib:x.y.z@code# rib aws topology by-nodes-per-instance \
    --linux-x86_64-clients-per-instance=7 \
    --linux-x86_64-servers-per-instance=5 \
    --linux-x86_64-instance-count=4
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
			Linux Clients: 7
			Linux Servers: 5
		Instance #2:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 7
			Linux Servers: 5
		Instance #3:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 7
			Linux Servers: 5
		Instance #4:
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 7
			Linux Servers: 5
```

## required args

### nodes-per-instance

At least one of the following nodes-per-instance parameters must be provided.

#### `--linux-x86_64-clients-per-instance INTEGER`

Maximum number of x86_64 Linux client nodes that may reside on a host.

#### `--linux-x86_64-server-per-instance INTEGER`

Maximum number of x86_64 Linux server nodes that may reside on a host.

#### `--linux-gpu-x86_64-clients-per-instance INTEGER`

Maximum number of x86_64 Linux GPU-enabled client nodes that may reside on a
host.

#### `--linux-gpu-x86_64-server-per-instance INTEGER`

Maximum number of x86_64 Linux GPU-enabled server nodes that may reside on a
host.

#### `--android-x86_64-clients-per-instance INTEGER`

Maximum number of x86_64 Android client nodes that may reside on a host.

#### `--linux-arm64-clients-per-instance INTEGER`

Maximum number of arm64 Linux client nodes that may reside on a host.

#### `--linux-arm64-server-per-instance INTEGER`

Maximum number of arm64 Linux server nodes that may reside on a host.

#### `--linux-gpu-arm64-clients-per-instance INTEGER`

Maximum number of arm64 Linux GPU-enabled client nodes that may reside on a
host.

#### `--linux-gpu-arm64-server-per-instance INTEGER`

Maximum number of arm64 Linux GPU-enabled server nodes that may reside on a
host.

#### `--android-arm64-clients-per-instance INTEGER`

Maximum number of arm64 Android client nodes that may reside on a host.

## optional args

#### `--colocate-clients-and-servers`, `--colocate`

Allow client and server nodes to reside on the same instances. By default,
each instance will be designated as hosting either clients or servers.

If using a fixed instance count, colocation must be enabled. It would not be
possible to determine how many instances should host clients vs servers based
purely on nodes-per-instance constraints.

#### `--format [json|yaml]`

If specified, the raw output format in which the AWS node-instance topology is
printed to the console.

#### `--out TEXT`

Location of file to which to write the AWS node-instance topology as a JSON
document.

### node counts

To automatically determine the required number of instances, at least one of the
following node count parameters must be provided.

These cannot be combined with any instance count parameter.

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

To automatically calculate the resulting number of RACE nodes if each instance
hosts its maximum number of nodes, at least one of the following instance count
parameters must be provided.

These cannot be combined with any node count parameter.

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
