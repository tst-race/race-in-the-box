# Tear Down an AWS Deployment

Tearing down an AWS deployment:
- Stops RACE node containers
- Stops comms channel and artifact manager plugin external services
- Stops bastion, opentracing, and RiB-specific orchestration services
- Removes plugin configs and runtime scripts

## syntax

```
rib deployment aws down <args>
```

## example

```
1) rib:x.y.z@code# rib deployment aws down --name=example-aws-deployment
```

## required args

#### `--name TEXT`

Name of the AWS deployment to tear down.

## optional args

#### `--purge`

By default, the docker images are left intact, allowing for the deployment to be
stood up again without re-downloading them. Setting this switch results in all
all docker images, networks, and volumes to be pruned.

#### `--timeout INTEGER`

*Default: 600*

Number of seconds to allow the deployment to tear down before timing out.

#### `--force`

By default, the down command will fail if the AWS deployment is determined to
already be in a down state. Setting this switch will force the tear down
operation to be re-executed.
