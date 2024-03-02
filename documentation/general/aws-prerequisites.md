## AWS Prerequisites

The below items are global prerequisites for utilizing AWS with RiB

## Table of Contents

* [AWS IAM User and Access Key](#aws-iam-user-and-access-key)
* [SSH Keys](#ssh-keys)
* [Start RiB](#start-rib)
* [Configure AWS Profile](#configure-aws-profile)

## AWS IAM User and Access Key

RiB utilizes the [AWS CLI](https://aws.amazon.com/cli/) to interacting with AWS.
An access key and secret key (tied to a user with the correct permissions) are
needed to connect RiB to AWS for creating and destroying resources.

Please follow the process to create a token/key
[here](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

These keys (access and secret) will be entered into RiB with the `rib aws init`
command

**NOTE** The following permissions are required for RiB AWS interaction as of
v2.0.0:

* CloudFormation
* EC2
* EFS
* IAM

More will be required as interactions between RiB and AWS increase in complexity
and new features are added (i.e. S3 may be required at some point)

### SSH Keys

AWS access is limited based on SSH access; please follow the guide
[here](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html#prepare-key-pair)
to create/import a key pair into AWS so that RiB can reference it when creating
environments.

***NOTE***: Please keep track of the name of the key pair, it will be used by
RiB commands.

### Configure AWS Profile

Using the key from [AWS IAM User and Access Key](#aws-iam-user-and-access-key),
we need to provide and configure RiB to work with AWS.

**{AWS_REGION}** should be set to the AWS region that your team wishes to deploy
to (depending on location and security constraints). Regions are defined
[here](https://aws.amazon.com/about-aws/global-infrastructure/regions_az/)

```
1) rib:x.y.z@code# rib aws init --access-key={ACCESS_KEY} --secret-key={SECRET_KEY} --region={AWS_REGION}
Initialize AWS Configuration
AWS Configuration Initialized
```

If you get an error about user permissions, please read
[AWS IAM User and Access Key](#aws-iam-user-and-access-key) to properly set up
your AWS account
