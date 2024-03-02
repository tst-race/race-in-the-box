# Report AWS Environment Runtime Info

Report the state of the EC2 instances running in an AWS environment, including:
- IP addresses
- tags
- running Docker containers

## syntax

```
rib env aws runtime-info <args>
```

## example

```
1) rib:x.y.z@code# rib env aws runtime-info --name=example-aws-env
android-node-host:
- containers: {}
  private_dns: ip-10-0-0-30.ec2.internal
  private_ip: 10.0.0.30
  public_dns: ec2-54-242-56-152.compute-1.amazonaws.com
  public_ip: 54.242.56.152
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: android-node-host
    Creator: rib
    Name: race-example-aws-env-android-node-host
    Stack: race-example-aws-env-android-node-host
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
gpu-node-host:
- containers: {}
  private_dns: ip-10-0-0-126.ec2.internal
  private_ip: 10.0.0.126
  public_dns: ec2-54-196-99-132.compute-1.amazonaws.com
  public_ip: 54.196.99.132
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: gpu-node-host
    Creator: rib
    Name: race-example-aws-env-gpu-node-host
    Stack: race-example-aws-env-gpu-node-host
    race_cost_service: RiB AWS Env
- containers: {}
  private_dns: ip-10-0-0-45.ec2.internal
  private_ip: 10.0.0.45
  public_dns: ec2-3-82-64-231.compute-1.amazonaws.com
  public_ip: 3.82.64.231
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: gpu-node-host
    Creator: rib
    Name: race-example-aws-env-gpu-node-host
    Stack: race-example-aws-env-gpu-node-host
    race_cost_service: RiB AWS Env
linux-node-host:
- containers: {}
  private_dns: ip-10-0-0-15.ec2.internal
  private_ip: 10.0.0.15
  public_dns: ec2-54-91-254-209.compute-1.amazonaws.com
  public_ip: 54.91.254.209
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: linux-node-host
    Creator: rib
    Name: race-example-aws-env-linux-node-host
    Stack: race-example-aws-env-linux-node-host
    race_cost_service: RiB AWS Env
- containers: {}
  private_dns: ip-10-0-0-28.ec2.internal
  private_ip: 10.0.0.28
  public_dns: ec2-3-81-34-247.compute-1.amazonaws.com
  public_ip: 3.81.34.247
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: linux-node-host
    Creator: rib
    Name: race-example-aws-env-linux-node-host
    Stack: race-example-aws-env-linux-node-host
    race_cost_service: RiB AWS Env
- containers: {}
  private_dns: ip-10-0-0-23.ec2.internal
  private_ip: 10.0.0.23
  public_dns: ec2-3-91-37-77.compute-1.amazonaws.com
  public_ip: 3.91.37.77
  tags:
    AwsEnvName: example-aws-env
    AwsEnvOwner: developer.name@company.com
    ClusterRole: linux-node-host
    Creator: rib
    Name: race-example-aws-env-linux-node-host
    Stack: race-example-aws-env-linux-node-host
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

When run on an AWS environment that is not active, nothing will be reported.

```
1) rib:x.y.z@code# rib env aws runtime-info --name=example-aws-env
android-node-host: []
cluster-manager: []
gpu-node-host: []
linux-node-host: []
service-host: []
```

## required args

#### `--name TEXT`

Name of the AWS environment for which to report runtime info. If no AWS
environment exists with the given name, the command will fail.

## optional args

#### `--format [json|yaml]`

*Default: yaml*

Specifies the output format in which the AWS environment runtime info is printed
to the console.
