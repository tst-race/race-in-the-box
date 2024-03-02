# Remove an AWS Environment

Remove an AWS environment and delete the
`~/.race/rib/aws-envs/<environment_name>/` directory.

## syntax

```
rib env aws remove <args>
```

## example

```
1) rib:x.y.z@code# rib env aws rename --name=example-aws-env
```

If you attempt to remove an AWS environment from an older version of RiB, you
will be prompted to confirm the deletion of the environment. This is because
RiB is unable to confirm that the environment is not still running in AWS
and would result in dangling AWS resources.

```
1) rib:x.y.z@code# rib env aws rename --name=old-aws-env
Removing AWS Environment: dummy-1-1-0
This AWS Environment was created with an older version of RiB. Are you sure you want to forcibly remove it? [y/N]: y
Removed AWS Environment: dummy-1-1-0
```

## required args

#### `--name TEXT`

Name of the AWS environment to be removed.

## optional args

None
