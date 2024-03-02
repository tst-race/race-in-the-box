## Copy an AWS Environment

Create a copy of an existing AWS environment, updating all occurrences of the
name if the new environment's metadata and configuration files.

## syntax

```
rib env aws copy <args>
```

## example

```
1) rib:x.y.z@code# rib env aws copy --from=orig-aws-env --to=copied-aws-env
```

## required args

#### `--from TEXT`

Name of the existing AWS environment to be copied. If no AWS environment exists
with the given name, the command will fail.

#### `--to TEXT`

Name to use for the copied AWS environment. If an AWS environment already exists
with the given name, the command will fail.

## optional args

#### `--force`

By default, the command will fail if the source AWS environment is currently
active (running in AWS). Setting this switch will force the copy to occur.
