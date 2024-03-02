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
        Config Command Group is responsible for generating and verifying configs
        for the RACE network.
"""

# Python Library Imports
import click

# Local Python Library Imports
from rib.utils import error_utils


###
# RiB Config Commands
###


@click.command("verify")
@click.pass_context
def verify(cli_context):
    """
    Verify a RiB Config
    """

    click.echo("Verify RiB Config")

    cli_context.obj.verify_rib_state()

    click.echo("RiB Config Verified")


@click.command("init")
@click.option(
    "--mode",
    "rib_mode",
    type=click.Choice(["local", "aws"], case_sensitive=False),
    default=None,
    required=False,
    help="What mode are you Running RiB in? (local or aws)",
)
@click.option(
    "--detail-level",
    default=None,
    type=click.IntRange(0, 5),
    required=False,
    help="What level of detail to use for output (0=least detailed, 5=most detailed)",
)
@click.option(
    "--verbosity",
    default=None,
    type=click.IntRange(0, 5),
    required=False,
    help="What level of logging verbosity to use (0=least verbose, 5=most verbose)",
)
@click.pass_context
def init(
    cli_context: object,
    rib_mode: str,
    detail_level: int,
    verbosity: int,
) -> None:
    """
    Initialize a Config
    """

    click.echo("Initalizing RiB Config")

    try:
        cli_context.obj.clear_rib_state()
        cli_context.obj.initalize_rib_state(
            rib_mode=rib_mode,
            detail_level=detail_level,
            verbosity=verbosity,
        )
        cli_context.obj.store_state()
    except Exception as err:
        raise error_utils.RIB002(err) from None

    click.echo("Initalized RiB Config")


@click.command("update")
@click.option(
    "--mode",
    "rib_mode",
    type=click.Choice(["local", "aws"], case_sensitive=False),
    default=None,
    required=False,
    help="What mode are you Running RiB in? (local or aws)",
)
@click.option(
    "--detail-level",
    default=None,
    type=click.IntRange(0, 5),
    required=False,
    help="What level of detail to use for output (0=least detailed, 5=most detailed)",
)
@click.option(
    "--verbosity",
    default=None,
    type=click.IntRange(0, 5),
    required=False,
    help="What level of logging verbosity to use (0=least verbose, 5=most verbose)",
)
@click.pass_context
def update(
    cli_context: object,
    rib_mode: str,
    detail_level: int,
    verbosity: int,
) -> None:
    """
    Update one or multiple config parameters
    """

    # Check if any config arguments (ignore cli_context since this is always passed and
    # is not part of the rib config) were passed (i.e not set to None). If not, print
    # the help menu for the command and return.
    was_any_arg_passed = any(
        [value is not None for key, value in locals().items() if key != "cli_context"]
    )
    if not was_any_arg_passed:
        click.echo(cli_context.get_help())
        return

    if rib_mode:
        cli_context.obj.set_rib_mode(rib_mode)
    if detail_level is not None:
        cli_context.obj.set_detail_level(detail_level)
    if verbosity is not None:
        cli_context.obj.set_verbosity(verbosity)

    cli_context.obj.store_state()

    click.echo("Updated RiB Config")


@click.command("list")
@click.pass_context
def list_config(cli_context):
    """
    List the stored state of RiB
    """

    stored_state = cli_context.obj.export_state()
    if stored_state:
        click.echo("RiB State:")
        for stored_state_key, stored_state_value in stored_state.items():
            click.echo(f"\t{stored_state_key} = {stored_state_value}")
    else:
        click.echo("Could not Get RiB State")
