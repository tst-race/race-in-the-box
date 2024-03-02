# List Active AWS Environments

List all AWS environments currently active in AWS under the AWS account.

## syntax

```
rib env aws active <args>
```

## example

```
1) rib:x.y.z@code# rib env aws active
Getting Active AWS Environments
My Active AWS Environments (launched by the current user/RiB instance):
	demo-aws-env
```

If other users have AWS environments running within the same AWS account, those
will also be listed.

```
1) rib:x.y.z@code# rib env aws active
Getting Active AWS Environments
My Active AWS Environments (launched by the current user/RiB instance):
	demo-aws-env
Other Active AWS Environments (launched by another user/RiB instance):
	not-my-aws-env
```

## required args

None

## optional args

None
