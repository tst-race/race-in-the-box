# Stand Up an AWS Deployment

Standing up an AWS deployment:
- Starts bastion, opentracing, and RiB-specific orchestration services on the
  cluster manager EC2 instance
- Starts comms channel and artifact manager plugin external services on the
  service host EC2 instance
- Uploads plugin configs and runtime scripts
- Uploads artifacts to artifact manager external services
- Starts RACE node containers
    - RACE daemon will be running but no RACE apps will be running

## syntax

```
rib deployment aws up <args>
```

## example

```
1) rib:x.y.z@code# rib deployment aws up --name=example-aws-deployment
```

## required args

#### `--name TEXT`

Name of the AWS deployment to stand up.

## optional args

#### `--no-publish`
Do not publish config tar files to the file server after upping the containers

#### `--timeout INTEGER`

*Default: 3600*

Number of seconds to allow the deployment to stand up before timing out.
Individual stand-up steps have their own timeouts (e.g., pulling
images), with this timeout representing the entire standing-up from start to
finish.

#### `--force`

By default, the up command will fail if the AWS deployment is determined to
already be in an up state. Setting this switch will force the stand up operation
to be re-executed.
