# Status of the Local Environment

The purpose of this command is to understand the status of the host machine and how that may affect a local deployment.

As of RiB 2.0.0 this is not an exhaustive list of factors that could affect a local deployment. More status information will be added in the future.

## syntax

```
rib env local status
```

## Example

```
rib:2.0.0@code# rib env local status
Using default detail level: 0
Docker Containers:
- race-in-the-box
rib:2.0.0@code#
```

## optional args

#### `-d`
*Default: 0*
Increase level of details in output

#### `--format`
Format output as JSON or YAML

