# Auditing and Managing AWS

This document will detail how to use RiB (and manually in some cases) audit
RiB's utilization of AWS.

## Steps

* [Prerequisites](#prerequisites)
* [Audit/Manage AWS](#audit-manage-aws)
    * [Get Active AWS Environments](#get-active-aws-environments)

## Prerequisites

Ensure that RiB has been configured to use your AWS account and all
[AWS prerequisites](../general/aws-prerequisites.md) are met.

## Audit/Manage AWS

Below are steps to audit RiB's utilization of AWS

### Get Active AWS Environments

RiB allows for querying and auditing AWS resources that have been created using
RiB on an account.

```
1) rib:x.y.z@code# rib env aws active
Getting Active AWS Environments
My Active AWS Envs (Launched By This RiB User/Instance):
    example-vabc-5client-10server-3workers
Other Active AWS Envs (Launched By Another RiB User/Instance):
    other-example-vabc-3client-3server-1workers
```

**My Active AWS Envs** are AWS environments that the RiB you are using controls
(and has config/metadata about). These can be upped/downed by RiB.

**Other Active AWS Envs** are AWS environments that the RiB you are using does
not have information/configs/metadata on. These were run from another RiB
instance and need to be manually managed or controlled by the RiB that was
responsible for standing these up.

*See the [`rib env aws active`](../reference/env/aws/active.md) reference for
additional details.*

### View Active RiB Environments from AWS UI

AWS offers a UI for interacting with AWS services, which can be helpful for
managing RiB.

[Filtered Cloudformation UI](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks?filteringText=race-&filteringStatus=active&viewNested=true&hideStacks=false&stackId=)

This view will show Cloudformation stacks (which group all RiB resources into
5-10 buckets) for an environment. Each environment create 5-10 stacks (depending
on host architecture and whether any GPU or Android nodes were specified in the
creation of the environment):

* `race-{AWS_ENV_NAME}-network`: Creates VPCs, subnets, internet gateways,
  security groups, etc
* `race-{AWS_ENV_NAME}-efs`: Creates /data EFS mount for shared
  data across all EC2 instances (and volume mounted into all containers)
* `race-{AWS_ENV_NAME}-cluster-manager`: Creates 1 EC2 instance for running
  Bastion, OpenTracing, and RiB-specific orchestration services
* `race-{AWS_ENV_NAME}-service-host`: Creates 1 EC2 instance for running comms
  channel and artifact manager plugin external services (e.g., whiteboards)
* `race-{AWS_ENV_NAME}-android-arm64-node-host`: Creates a fixed-size autoscale
  group of EC2 instances for running RACE Android arm64 client nodes (if
  specified)
* `race-{AWS_ENV_NAME}-android-x86-64-node-host`: Creates a fixed-size autoscale
  group of EC2 instances for running RACE Android x86_64 client nodes (if
  specified)
* `race-{AWS_ENV_NAME}-linux-gpu-arm64-node-host`: Creates a fixed-size
  autoscale group of EC2 instances for running RACE GPU-enabled Linux arm64
  nodes (if specified)
* `race-{AWS_ENV_NAME}-linux-gpu-x86-64-node-host`: Creates a fixed-size
  autoscale group of EC2 instances for running RACE GPU-enabled Linux x86_64
  nodes (if specified)
* `race-{AWS_ENV_NAME}-linux-arm64-node-host`: Creates a fixed-size autoscale
  group of EC2 instances for running RACE non-GPU Linux arm64 nodes (if
  specified)
* `race-{AWS_ENV_NAME}-linux-x86-64-node-host`: Creates a fixed-size autoscale
  group of EC2 instances for running RACE non-GPU Linux x86_64 nodes (if
  specified)

All AWS services are created from CloudFormation. If you need to manually stop
any AWS services externally from RiB; you can destroy these stacks. Once they
have been fully deleted, there should be no services running in AWS and no more
charges should be accrued.
