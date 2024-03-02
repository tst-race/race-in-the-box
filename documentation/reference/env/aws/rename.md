# Rename an AWS Environment

Rename an AWS environment and update all occurrences of the name in the
metadata and configuration files.

## syntax

```
rib env aws rename <args>
```

## example

```
1) rib:x.y.z@code# rib env aws rename --from=old-aws-env --to=new-aws-env
```

## required args

#### `--from TEXT`

Name of the existing AWS environment to be renamed. If no AWS environment exists
with the given name, the command will fail.

#### `--to TEXT`

New name to use for the renamed AWS environment. If an AWS environment already
exists with the given name, the command will fail.
