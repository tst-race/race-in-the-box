# Provision an AWS Environment

Provisioning an AWS environment will:
- Create all AWS resources (CloudFormation stacks, networks, EFS volumes, EC2
  instances)
- Configure the EC2 instance hosts in order to host a RACE deployment
    - Mount EFS volumes
    - Install and configure docker

RiB uses ansible to interact with AWS to create the AWS resources and to
perform configuration of the EC2 instances. The provision operation is then
idempotent and can be re-run if an error occurs during the provisioning of the
environment.

## syntax

```
rib env aws provision <args>
```

## example

```
1) rib:x.y.z@code# rib env aws provision --name=demo-aws-env
```

## required args

#### `--name TEXT`

Name of the AWS environment to provision.

## optional args

#### `--timeout INTEGER`

*Default: 3600*

Number of seconds to allow the provision operation to run before timing out.
Individual provisioning steps have their own timeouts (e.g., package
installation), with this timeout representing the entire provisioning from
start to finish.

#### `--force`

By default, the provision command will fail if the AWS environment is already
determined to be in a ready state. Setting this switch will force the
provision operation to be re-executed.
