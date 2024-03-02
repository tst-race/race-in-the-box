# Set the Node(s) Local Timezone

Set the timezone on the node(s), so local time can be used

## Syntax

```
rib deployment <mode> set-timezone <args>
```

## Example

```
1) rib:x.y.z@code# rib deployment local set-timezone --name=example-deployment --zone=EDT --node=race-client-0000*
```

```
2) rib:x.y.z@code# rib deployment local set-timezone --name=example-deployment --local-time=15 --node=race-client-00001
```

```
3) rib:x.y.z@code# rib deployment local set-timezone --name=example-deployment --zone=America/Creston --node=race-client-0000[0-9]
```

## Required State
Nodes must be stood up, but cannot be started/running. A running node cannot be changed, so stop any nodes that you wish to change before running the command. Once restarted, any affected node's time should be different.

## Required Args

#### --name TEXT
The name of the deployment to modify

## Mutually Exclusive Args

#### --zone TEXT
The new timezone that will be written to each targeted node
List of valid timezones found here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

#### --local-time INT
The new local time that will be written to each targeted node as the hour of the day (0-24)

## Optional Args

#### --node TEXT
The name of the node(s) to be altered. If excluded, new local time(zone) is enacted on all nodes. Otherwise, change is applied to the specified subset of nodes
