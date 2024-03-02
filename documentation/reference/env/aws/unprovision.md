# Unprovision an AWS Environment

Unprovisioning an AWS environment will remove all AWS resources.

After unprovisioning, nothing will be left in AWS so no further AWS billing
costs can be accrued.

## syntax

```
rib env aws unprovision <args>
```

## example

```
1) rib:x.y.z@code# rib env aws unprovision --name=example-aws-env
```

## required args

#### `--name TEXT`

Name of the AWS environment to unprovision.

## optional args

#### `--timeout INTEGER`

*Default: 600*

Number of seconds to allow for each CloudFormation stack to be deleted before
timing out.

#### `--force`

By default, the unprovision command will fail if the AWS environment is detected
as hosting a running deployment (i.e., there are running Docker containers).
Setting this switch will force the unprovision operation to run.

```
1) rib:x.y.z@code# rib env aws unprovision --name=demo-aws-env
Unprovisioning AWS Environment: demo-aws-env
rib.utils.error_utils.RIB723: 
	Error Code: RIB723
	Message: Unable to unprovision demo-aws-env, currently in use by a deployment
	Suggestion: Tear down the deployment or use the `--force` flag to unprovision anyway
1) rib:x.y.z@code# rib env aws unprovision --name=demo-aws-env --force
```
