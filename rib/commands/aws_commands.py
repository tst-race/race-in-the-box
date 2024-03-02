# Copyright 2023 Two Six Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
    Purpose:
        AWS Command Group is responsible for configuring and initializing
        AWS and RiB Connectivity
"""

# Python Library Imports
import click
import getpass

# Local Python Library Imports
from rib.utils import aws_utils


###
# AWS Commands
###


@click.command("init")
@click.option(
    "--access-key",
    "access_key",
    required=False,
    default=None,
    help="Access Key for AWS account to use with RiB",
)
@click.option(
    "--secret-key",
    "secret_key",
    required=False,
    default=None,
    help="Secret Key for AWS account to use with RiB",
)
@click.option(
    "--region",
    "aws_region",
    type=click.Choice(
        ["us-east-1", "us-east-2", "us-west-1", "us-west-2"], case_sensitive=True
    ),
    default="us-east-1",
    required=False,
    help="Default region for AWS operations",
)
@click.option(
    "--overwrite",
    "overwrite",
    flag_value=True,
    help="Overwrite existing profile if present?",
)
@click.option(
    "--linux-x86-64-ami",
    "linux_x86_64_ami",
    default=None,
    required=False,
    help="AMI ID for linux-x86-64 instances",
)
@click.option(
    "--linux-arm64-ami",
    "linux_arm64_ami",
    default=None,
    required=False,
    help="AMI ID for linux-arm64 instances",
)
@click.option(
    "--linux-gpu-x86-64-ami",
    "linux_gpu_x86_64_ami",
    default=None,
    required=False,
    help="AMI ID for linux-gpu-x86-64 instances",
)
@click.option(
    "--linux-gpu-arm64-ami",
    "linux_gpu_arm64_ami",
    default=None,
    required=False,
    help="AMI ID for linux-gpu-arm64 instances",
)
@click.pass_context
def init(
    cli_context: object,
    access_key: str,
    secret_key: str,
    aws_region: str,
    overwrite: bool,
    linux_x86_64_ami: str,
    linux_arm64_ami: str,
    linux_gpu_x86_64_ami: str,
    linux_gpu_arm64_ami: str,
) -> None:
    """
    Initialize AWS profile and settings in RiB
    """
    click.echo(f"Initialize AWS Configuration")

    # Getting values from prompt if they are not passed in
    if not access_key:
        access_key = click.prompt("Please Enter AWS Access Key ID", type=str)
    if not secret_key:
        secret_key = getpass.getpass("Please Enter AWS Secret Key: ")

    # Create and verify profile
    aws_utils.create_aws_profile(
        access_key,
        secret_key,
        aws_region,
        overwrite,
        linux_x86_64_ami,
        linux_arm64_ami,
        linux_gpu_x86_64_ami,
        linux_gpu_arm64_ami,
    )

    click.echo(f"AWS Configuration Initialized")


@click.command("info")
@click.pass_context
def info(cli_context: object) -> None:
    """
    Get Information about AWS configuration and credentials
    """
    click.echo(f"Getting AWS Information for RiB")

    aws_profile_information = aws_utils.get_aws_profile_information()

    click.echo(f"AWS Information: ")
    for key, value in aws_profile_information.items():
        click.echo(f"\t{key}: {value}")


@click.command("verify")
@click.pass_context
def verify(cli_context: object) -> None:
    """
    Verify AWS connectivity/profile/permissions with RiB
    """
    click.echo(f"Verifying AWS Configuration")

    aws_utils.verify_aws_profile()

    click.echo(f"AWS Configuration Verified")
