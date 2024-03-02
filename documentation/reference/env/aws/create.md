# Create an AWS Environment

An **AWS environment** consists of:
- Ansible playbooks
- CloudFormation templates
- Environment metadata

Creating an AWS environment gathers/creates the required files and places them
in a new environment directory `~/.race/rib/aws-envs/<environment_name>/`.

## syntax

```
rib env aws create <args>
```

## example

```
1) rib:x.y.z@code# rib env aws create \
    --name=example-aws-env \
    --ssh-key-name=race-developer_name \
    --android-x86_64-instance-count=1 \
    --linux-gpu-x86_64-instance-count=2 \
    --linux-x86_64-instance-count=3
Creating AWS Environment: example-aws-env
AWS Environment will be created with:
	1 c5.metal EC2 instances for RACE nodes
	2 p3.2xlarge EC2 instances for RACE nodes
	3 t3a.2xlarge EC2 instances for RACE nodes
	1 t3a.2xlarge EC2 instance as the cluster manager
	1 t3a.2xlarge EC2 instance as the external service host
Do you want to proceed? [y/N]: y
Created AWS Environment: example-aws-env
```

## required args

#### `--name TEXT`

The name of the AWS environment. This is used for the directory name and is
required for other operations on the environment.

The name can only contain alphanumeric characters and the `-` character due to
Amazon's naming restrictions (as documented
[here](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cfn-using-console-create-stack-parameters.html)).

#### `--ssh-key-name TEXT`

The name of the SSH key pair that has been preloaded in AWS as per the
[prequisites](aws-prerequisites.md).

## optional args

#### `--region TEXT`

*Default: us-east-1*

AWS region in which to create the deployment. Your AWS account must be
authorized for the region and it should match the value used in the
`rib aws init` command.

#### `--force`

By default the create command will fail if there is already an AWS
environment/directory of the same name in `~/.race/rib/aws-envs/`. Setting this
switch will overwrite the existing environment.

#### `-y, --yes`

By default, the create command will prompt the user to confirm the number of
EC2 instances that will be defined in the AWS environment. Setting this switch
will automatically confirm the prompt.

### instance count args

At least one of the following must be specified.

#### `--android-x86_64-instance-count INTEGER`

*Default: 0*

Number of Android x86_64 RACE node host EC2 instances to create in the
environment.

#### `--linux-gpu-x86_64-instance-count INTEGER`

*Default: 0*

Number of GPU-enabled Linux x86_64 RACE node host EC2 instances to create in the
environment.

#### `--linux-x86_64-instance-count INTEGER`

*Default: 0*

Number of Linux x86_64 RACE node host EC2 instances to create in the
environment.

#### `--android-arm64-instance-count INTEGER`

*Default: 0*

Number of Android arm64 RACE node host EC2 instances to create in the
environment.

#### `--linux-gpu-arm64-instance-count INTEGER`

*Default: 0*

Number of GPU-enabled Linux arm64 RACE node host EC2 instances to create in the
environment.

#### `--linux-arm64-instance-count INTEGER`

*Default: 0*

Number of Linux arm64 RACE node host EC2 instances to create in the
environment.

#### `--topology TEXT`

Path to a node topology JSON file output from a `rib aws topology` command, to
specify the number of Android, GPU, and Linux RACE node host EC2 instances to
create in the environment.

### instance type args

See https://aws.amazon.com/ec2/instance-types/ for specifications for each EC2 instance type.

#### `--android-arm64-instance-type TEXT`

*Default: a1.metal*

EC2 instance type for Android arm64 RACE node hosts. The EC2 instance type must
be a metal graviton type.

#### `--android-x86_64-instance-type TEXT`

*Default: c5.metal*

EC2 instance type for Android x86_64 RACE node hosts. The EC2 instance type must
be a metal type.

#### `--linux-gpu-x86_64-instance-type TEXT`

*Default: p3.2xlarge*

EC2 instance type for GPU-enabled Linux x86_64 RACE node hosts. The EC2 instance
type must have GPU cards.

#### `--linux-gpu-arm64-instance-type TEXT`

*Default: g5g.2xlarge*

EC2 instance type for GPU-enabled Linux arm64 RACE node hosts. The EC2 instance
type must have GPU cards and be a graviton type.

#### `--linux-x86_64-instance-type TEXT`

*Default: t3a.2xlarge*

EC2 instance type for Linux x86_64 RACE node hosts.

#### `--linux-arm64-instance-type TEXT`

*Default: t4g.xlarge*

EC2 instance type for Linux arm64 RACE node hosts. The EC2 instance type must be
a graviton type.

#### `--cluster-manager-instance-type TEXT`

*Default: t3a.2xlarge*

EC2 instance type for the AWS environment cluster manager that will host
bastion, opentracing, and RiB-specific deployment orchestration services.

#### `--service-host-instance-type TEXT`

*Default: t3a.2xlarge*

EC2 instance type for the instance that will host comms channel and artifact
manager plugin external services.

### instance EBS size args

#### `--android-instance-ebs-size INTEGER`

*Default: 128*

Size of the EBS volume in GB for all Android RACE node host instances.

#### `--linux-gpu-instance-ebs-size INTEGER`

*Default: 128*

Size of the EBS volume in GB for all GPU-enabled Linux RACE node host instances.

#### `--linux-instance-ebs-size INTEGER`

*Default: 64*

Size of the EBS volume in GB for all Linux RACE node host instances.

#### `--cluster-manager-instance-ebs-size INTEGER`

*Default: 64*

Size of the EBS volume in GB for the cluster manager instance.

#### `--service-host-instance-ebs-size INTEGER`

*Default: 64*

Size of the EBS volume in GB for the external service host instance.
