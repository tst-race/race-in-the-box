## List Local AWS Environments

List all AWS environments defined and existing in `~/.race/rib/aws-envs/`.

## syntax

```
rib env aws list
```

## example

```
1) rib:x.y.z@code# rib env aws list
Compatible AWS Environments:
        demo-aws-env
```

If you have any AWS environments from older versions of RiB, they will be listed
along with their corresponding version of RiB.

```
1) rib:x.y.z@code# rib env aws list
Compatible AWS Environments:
        demo-aws-env
Incompatible AWS Environments (from previous RiB versions):
        old-aws-env (RiB a.b.c)
```

## required args

none

## optional args

none
