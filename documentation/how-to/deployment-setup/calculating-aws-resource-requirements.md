# Calculating Required AWS Resources

When creating an AWS environment, you must determine how many EC2 instances will
be running. The `rib aws topology by-node-resource-requirements` command can be
used to experiment with different resource values and preview the RACE node
distribution, or topology. Once you are satisfied with the RACE node topology,
you can use the instance counts (and any non-default instance types) with the
`rib env aws create` command.

***NOTE*** If you are running with a large number of RACE nodes (clients and
servers) or are running particularly resource intensive plugins you may need to
change the instance type to something more powerful or increase the number of
instances to help distribute the load.

RiB will create the following EC2 instances in an AWS environment:

* A cluster manager instance to run Bastion, OpenTracing, and other RiB-specific
  deployment orchestration services
* An external services host instance to run whiteboards, etc. as needed by comms
  channels and artifact manager plugins
* Android node hosts to run RACE Android client nodes
* GPU-enabled node hosts to run RACE Linux client or server nodes with GPU
  support
* Linux node hosts to run RACE Linux client or server nodes (with no GPU
  support)

The instance types used for each class of instance can be set by the user to an       
[EC2 instance type](https://aws.amazon.com/ec2/instance-types/) supported by
AWS.

* The instance type for the cluster manager instance and the service host
  instance is set with the `--service-instance-type` option.
* The instance types for Android node host instances is set with the
  `--android-x86_64-instance-type` or `--android-arm64-instance-type` options.
* The instance type for the GPU node host instances is set with the
  `--linux-gpu-x86_64-instance-type` or
  `--linux-gpu-arm64-instance-type` options.
* The instance type for the Linux node host instances is set with the
  `--linux-x86_64-instance-type` or `--linux-arm64-instance-type` options.

The resource calculation will only allocate Android node host instances if you
have specified an Android client count. Similarly, it will only allocate GPU
node host instances if you have specified that any clients or servers will have
GPU support.

RiB will use RAM and CPU requirements of RACE nodes and the available
RAM and CPU of each instance type to calculate the number of required instances.
The following options can be set to tweak the resource calculations (all options
have sane default values, run
`rib aws topology by-node-resource-requirements --help` to see the current
default values):

* `--ram-per-android-client`
* `--ram-per-linux-client`
* `--ram-per-linux-server`
* `--ram-overcommit`
* `--cpus-per-android-client`
* `--cpus-per-linux-client`
* `--cpus-per-linux-server`
* `--cpu-overcommit`
* `--gpus-per-android-client`
* `--gpus-per-linux-client`
* `--gpus-per-linux-server`
* `--gpu-overcommit`

RiB will distribute all specified RACE nodes across the calculated number of EC2
instances. By default, instances will be determined to host either client or
server nodes. You can set the `--colocate` switch to place clients and servers
on the same host. This allow allows for Android or GPU-eanbled instances to host
additional Linux nodes if there are remaining resources.

The `--ram-overcommit` and `--cpu-overcommit` options allow for specifying a
fraction of the required RAM or CPU for a node to be shared with other nodes on
the same host. For example, if client nodes require 4096 MB of RAM the default
is to allocate the full 4096 MB for each client node assigned to a host. If the
RAM per node is a peak usage rather than the nominal usage, setting a RAM
overcommit fraction may result in more nodes being assiged to a host. For
example, using a RAM overcommit fraction of 0.1 and 4096 MB of RAM per node,
each node will be allocated a guaranteed 3686 MB of RAM and 410 MB on each
instance host will be available for nodes for peak usage.

***NOTE***: RiB will not place any hard RAM or CPU limits on the RACE node
containers. These resource requirements are only used to calculate the optimal
number of EC2 instance hosts to run the specified number of RACE nodes.

```
1) rib:x.y.z@code# rib aws topology by-node-resource-requirements \
    --android-x86_64-client-count=3 \
    --linux-x86_64-client-count=10 \
    --linux-x86_64-server-count=16 \
    --linux-gpu-x86_64-server-count=4 \
	--gpu-overcommit=1.0
AWS Node Instance Topology:
	android arm64 instances:
	android x86_64 instances:
		Instance #1:
			EC2 instance type: c5.metal
			Android Clients: 3
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 0
			Linux Servers: 0
			RAM utilization: 12288.0/196608.0 (6.2%)
			CPU utilization: 3.0/96.0 (3.1%)
	linux GPU-enabled arm64 instances:
	linux GPU-enabled x86_64 instances:
		Instance #2:
			EC2 instance type: p3.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 4
			Linux Clients: 0
			Linux Servers: 0
			RAM utilization: 16384.0/62464.0 (26.2%)
			CPU utilization: 4.0/8.0 (50.0%)
			GPU utilization: 1.0/1.0 (100.0%)
	linux arm64 instances:
	linux x86_64 instances:
		Instance #3:
			EC2 instance type: t3a.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 0
			Linux Servers: 7
			RAM utilization: 28672.0/32768.0 (87.5%)
			CPU utilization: 7.0/8.0 (87.5%)
		Instance #4:
			EC2 instance type: t3a.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 0
			Linux Servers: 7
			RAM utilization: 28672.0/32768.0 (87.5%)
			CPU utilization: 7.0/8.0 (87.5%)
		Instance #5:
			EC2 instance type: t3a.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 0
			Linux Servers: 2
			RAM utilization: 8192.0/32768.0 (25.0%)
			CPU utilization: 2.0/8.0 (25.0%)
		Instance #6:
			EC2 instance type: t3a.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 7
			Linux Servers: 0
			RAM utilization: 28672.0/32768.0 (87.5%)
			CPU utilization: 7.0/8.0 (87.5%)
		Instance #7:
			EC2 instance type: t3a.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 3
			Linux Servers: 0
			RAM utilization: 12288.0/32768.0 (37.5%)
			CPU utilization: 3.0/8.0 (37.5%)

1) rib:x.y.z@code# rib aws topology by-node-resource-requirements \
    --android-x86_64-client-count=3 \
    --linux-x86_64-client-count=10 \
    --linux-x86_64-server-count=16 \
    --linux-gpu-x86_64-server-count=4 \
	--gpu-overcommit=1.0 \
	--colocate
AWS Node Instance Topology:
	android arm64 instances:
	android x86_64 instances:
		Instance #1:
			EC2 instance type: c5.metal
			Android Clients: 3
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 0
			Linux Clients: 10
			Linux Servers: 16
			RAM utilization: 118784.0/196608.0 (60.4%)
			CPU utilization: 29.0/96.0 (30.2%)
	linux GPU-enabled arm64 instances:
	linux GPU-enabled x86_64 instances:
		Instance #2:
			EC2 instance type: p3.2xlarge
			Android Clients: 0
			Linux GPU-enabled Clients: 0
			Linux GPU-enabled Servers: 4
			Linux Clients: 0
			Linux Servers: 0
			RAM utilization: 16384.0/62464.0 (26.2%)
			CPU utilization: 4.0/8.0 (50.0%)
			GPU utilization: 1.0/1.0 (100.0%)
	linux arm64 instances:
	linux x86_64 instances:
```
