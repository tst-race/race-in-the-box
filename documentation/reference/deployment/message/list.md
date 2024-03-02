# List Messages
List messages sent on the deployment

## syntax

```
rib deployment <mode> message list <args>
```

## Example
```
rib:x.y.z@code# rib deployment local message list --name=example-deployment
+------------------+---------+------+-------------------+-------------------+----------+---------------------+---------------------+-----------------+
|     Trace ID     | Test ID | Size |       Sender      |     Recipient     |  Status  |      Start Time     |       End Time      | Total Time (μs) |
+------------------+---------+------+-------------------+-------------------+----------+---------------------+---------------------+-----------------+
| 0bcad6f1b9725490 | default |  10  | race-client-00004 | race-client-00003 | received | 2022-03-30 14:19:58 | 2022-03-30 14:20:02 |     4299007     |
| 1841b90ad01840df | default |  13  | race-client-00001 | race-client-00002 | received | 2022-03-31 19:58:08 | 2022-03-31 19:58:11 |     3283856     |
| b37353f2c7c571e6 | default |  10  | race-client-00002 | race-client-00004 | received | 2022-03-30 14:19:44 | 2022-03-30 14:19:46 |     1877527     |
+------------------+---------+------+-------------------+-------------------+----------+---------------------+---------------------+-----------------+
rib:x.y.z@code#
```

## required args

#### --name TEXT
The name of the deployment to send messages on

## optional args

#### --recipient TEXT
Filter message list based on the recipient

#### --sender TEXT
Filter message list based on the sender

#### --test-id TEXT
Filter message list based on the test-id

#### --trace-id TEXT
Filter message list based on the trace-id

#### --sort-by TEXT
Sort the list based on a specific column (must match an existing column)

#### --reverse-sort
Reverse the order of the list

