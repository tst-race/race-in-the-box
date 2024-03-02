# Generate Configs

Generating Configs:
- Calls scripts from the Network Manager, Comms, and Artifact Manager plugins to
generate their configs in coordination with each other
- Creates user-responses file used to automate queries to the user from plugins
- Tars config and etc files for each node unles `--no-tar` is supplied as an option 

## Syntax

```
rib deployment <mode> config generate <args>
```

## Example

Minimum required arguments

```
rib deployment local config generate \
    --name example-deployment \
```

Custom plugin arguments

```
rib deployment local config generate \
    --name example-deployment \
    --network-manager-custom-args "--arg1=value --arg2" \
    --comms-custom-args '{"channel_id":"--arg1=value --arg2"}'
```

## Arguments

### Required

`--name TEXT`

Name of the deployment for which to generate configs.

### Optional

`--force`

Deletes existing configs prior to re-running config generation. It also ignores
any precondition status checks.

`--network-manager-custom-args TEXT`

Custom arguments for the network manager plugin's config generation script. 

Example: `--network-manager-custom-args="--arg1=value --arg2 ..."`

`--comms-custom-args TEXT`

JSON map of comms channel IDs to custom arguments for the channel's config
generation script. 

Example: `--comms-custom-args='{"channel_id":"--arg1=value --arg2..."}'`

`--artifact-manager-custom-args TEXT`

JSON map of argifact manager plugin IDs to custom arguments for the plugins's
config generation script. 

Example: `--artifact-manager-custom-arg='{"plugin_id":"--arg1=value --arg2..."}'`

`--no-tar`

Disables creation of tar configs after config generation.

`--max-iterations INTEGER RANGE`

*Default: 20*

Number of iterations to allow between network manager and comms config
generation (1<=x<=100)

`--timeout INTEGER`

*Default: 300*

Number of seconds to allow this action to execute before timing out
