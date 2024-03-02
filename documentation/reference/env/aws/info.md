# Report AWS Environment Info

Report the configuration and metadata for an AWS environment.

This command can be run at any time and does not require the environment to be
running in AWS.

## syntax

```
rib env aws info <args>
```

## example

```
1) rib:x.y.z@code# rib env aws info --name=example-aws-env
config:
  android_hosts:
    ebs_size: 128
    instance_arch: x86
    instance_count: 1
    instance_type: c5.metal
  cluster_manager:
    ebs_size: 64
    instance_arch: x86
    instance_type: t3a.2xlarge
  gpu_hosts:
    ebs_size: 128
    instance_arch: x86
    instance_count: 2
    instance_type: p3.2xlarge
  linux_hosts:
    ebs_size: 64
    instance_arch: x86
    instance_count: 3
    instance_type: t3a.2xlarge
  name: example-aws-env
  region: us-east-1
  remote_username: rib
  rib_version: x.y.z
  service_host:
    ebs_size: 64
    instance_arch: x86
    instance_type: t3a.2xlarge
  ssh_key_name: race-developer_name
metadata:
  create_command: rib env aws create  --name=example-aws-env --ssh-key-name=race-developer_name --android-instance-count=1 --linux-gpu-instance-count=2 --linux-instance-count=3 --region=us-east-1 --android-arm-instance-type=a1.metal --android-x86-instance-type=c5.metal --linux-node-instance-type=t3a.2xlarge --linux-gpu-node-instance-type=p3.2xlarge --cluster-manager-instance-type=t3a.2xlarge --service-instance-type=t3a.2xlarge --android-node-instance-ebs-size=128 --linux-node-instance-ebs-size=64 --linux-gpu-node-instance-ebs-size=128 --cluster-manager-instance-ebs-size=64 --service-instance-ebs-size=64 --android-arch=x86
  create_date: '2022-01-19T16:44:08.796679'
  last_provision_command: null
  last_provision_time: null
  last_unprovision_command: null
  last_unprovision_time: null
  last_used_amis: null
  rib_image:
    created: '2022-01-18T21:14:18.438222605Z'
    digest: ghcr.io/tst-race/race-in-the-box/race-in-the-box@sha256:2e7750ec9ddbfbf3280d01716fd1ce940b6ecbca88ade946e1323831f79b0e5f
    tag: ghcr.io/tst-race/race-in-the-box/race-in-the-box:x.y.z
```

## required args

#### `--name TEXT`

Name of the AWS environment for which to report info. If no AWS environment
exists with the given name, the command will fail.

## optional args

#### `--format [json|yaml]`

*Default: yaml*

Specifies the output format in which the AWS environment info is printed to the
console.
