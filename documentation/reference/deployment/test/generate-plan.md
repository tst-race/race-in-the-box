# Generate Test Plan

Generate the default test plan JSON for a deployment. By default, it is printed
to the console as escaped JSON that could be used with the `--test-plan-json`
argument of the [`test integrated`](./integrated.md) or the
[`test comms-channel`](./comms-channel.md) commands.

## syntax

```
rib deployment <mode> test generate-plan <args>
```

## example

```
1) rib:x.y.z@code# rib deployment local test generate-plan --name=example-deployment
Generating Test Plan File
Escaped Test Plan: "{\"clients\": [\"race-client-00001\", ...
```

## required args

#### `--name TEXT`

Name of the deployment for which to generate a test plan.

## optional args

Most of the optional arguments of the [`test integrated`](./integrated.md) and
[`test comms-channel`](./comms-channel.md) are applicable to this command.

The following arguments are specific to this command.

#### `--output-file TEXT`

In addition to printing the test plan JSON to the console, write the test plan
to the specified file.

#### `--overwrite-file`

Normally the command will fail if the destination output file already exists.
This flag allows for writing of an existing output file.

#### `--raw`

Normally the test plan JSON is printed to the console as escaped JSON. This is
useful for copying and using as the `--test-plan-json` argument to the
`test integrated` and `test comms-channel` commands. This flag enables un-escaped,
pretty printing of the JSON.
