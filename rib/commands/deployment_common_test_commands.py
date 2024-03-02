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
    Common deployment test commands
"""

# Python Library Imports
import click

from rib.commands.deployment_options import (
    deployment_name_option,
    pass_rib_mode,
)
from rib.commands.testing_options import (
    debug_option,
    delay_evaluation_option,
    delay_execute_option,
    delay_start_option,
    start_timeout_option,
    evaluation_interval_option,
    is_running_option,
    no_down_option,
    raise_on_fail_option,
    run_time_option,
    test_plan_file_option,
    test_plan_json_option,
)
from rib.deployment.rib_deployment import RibDeployment
from rib.utils import error_utils, general_utils
from rib.utils.testing_utils import RaceTest

###
# Generic Deployment Test Commands
###


@click.group("test")
def test_command_group() -> None:
    """Commands for testing a deployment"""


@test_command_group.command("integrated")
@deployment_name_option("run")
@test_plan_file_option()
@test_plan_json_option()
@run_time_option()
@is_running_option()
@delay_evaluation_option()
@delay_execute_option()
@delay_start_option()
@start_timeout_option()
@evaluation_interval_option()
@raise_on_fail_option()
@debug_option()
@no_down_option()
@click.pass_context
@pass_rib_mode
def integrated(
    cli_context: click.core.Context,
    deployment_name: str,
    test_plan_file: str,
    test_plan_json: str,
    rib_mode: str,
    run_time: int,
    is_running: bool,
    raise_on_fail: bool,
    delay_evaluation: int,
    delay_execute: int,
    delay_start: int,
    start_timeout: int,
    debug: bool,
    evaluation_interval: int,
    no_down: bool,
) -> None:
    """
    Run RiB Deployment Test
    """
    """
    Test a specified deployment against expectations
    """
    click.echo(f"Testing Deployment: {deployment_name} (test-plan = {test_plan_file})")

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Generate the test plan (let utils decide the method)
    race_test = RaceTest(
        deployment,
        run_time=run_time,
        delay_evaluation=delay_evaluation,
        delay_execute=delay_execute,
        delay_start=delay_start,
        start_timeout=start_timeout,
        evaluation_interval=evaluation_interval,
        is_running=is_running,
        test_plan_file=test_plan_file,
        test_plan_json=test_plan_json,
        comms_channel=None,
        comms_channel_type=None,
        network_manager_bypass=False,
        no_down=no_down,
    )

    if not race_test.test_config.is_running and deployment.bridge_personas:
        click.confirm(
            "Running a test with bridged nodes will fail. Would you like to continue anyway?",
            abort=True,
        )

    # Verify that the test plan that was generated has the correct
    # bypass/channel settings
    if (
        race_test.test_config.network_manager_bypass
        or race_test.test_config.comms_channel
        or race_test.test_config.comms_channel_type
    ):
        raise error_utils.RIB603(
            race_test.export_plan_to_dict(),
            "Deployment tests must not have network_manager_bypass, comms_channel, comms_channel_type",
        )

    # Run the tests
    race_test.run_deployment_test(cli_context=cli_context)

    # Print the test report
    race_test.print_report()

    # If debug, going to create breakpoint for inspecting results
    if debug:
        breakpoint()

    # If `--raise-on-fail set and there are failures, raise exception
    if raise_on_fail and race_test.failed:
        raise error_utils.RIB601(deployment_name, race_test)


@test_command_group.command("comms-channel")
@deployment_name_option("test")
@test_plan_file_option()
@test_plan_json_option()
@run_time_option()
@is_running_option()
@delay_evaluation_option()
@delay_execute_option()
@delay_start_option()
@start_timeout_option()
@evaluation_interval_option()
@raise_on_fail_option()
@debug_option()
@no_down_option()
@pass_rib_mode
@click.option(
    "--comms-channel",
    "comms_channel",
    required=True,
    type=str,
    help="What channel to use with network-manager-bypass (focus of the test)",
)
@click.option(
    "--comms-channel-type",
    "comms_channel_type",
    required=True,
    type=click.Choice(["c2s", "s2s", "all"], case_sensitive=True),
    help="Type of channel",
)
@click.pass_context
def comms_channel(
    cli_context: click.core.Context,
    deployment_name: str,
    test_plan_file: str,
    test_plan_json: str,
    rib_mode: str,
    run_time: int,
    is_running: bool,
    raise_on_fail: bool,
    delay_evaluation: int,
    delay_execute: int,
    delay_start: int,
    start_timeout: int,
    debug: bool,
    evaluation_interval: int,
    comms_channel: str,
    comms_channel_type: str,
    no_down: bool,
):
    """
    Test a specified comms channel against expectations
    """
    click.echo(
        f"Testing Comms Channel: {comms_channel} (deployment = {deployment_name},"
        f" test-plan = {test_plan_file})"
    )

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Validate that the channel being tested is valid
    if comms_channel not in [x["name"] for x in deployment.config["comms_channels"]]:
        raise error_utils.RIB602(deployment_name, comms_channel)

    # Generate the test plan (let utils decide the method)
    race_test = RaceTest(
        deployment,
        run_time=run_time,
        delay_evaluation=delay_evaluation,
        delay_execute=delay_execute,
        delay_start=delay_start,
        start_timeout=start_timeout,
        evaluation_interval=evaluation_interval,
        is_running=is_running,
        test_plan_file=test_plan_file,
        test_plan_json=test_plan_json,
        comms_channel=comms_channel,
        comms_channel_type=comms_channel_type,
        network_manager_bypass=True,
        no_down=no_down,
    )

    if not race_test.test_config.is_running and deployment.bridge_personas:
        click.confirm(
            "Running a test with bridged nodes will fail. Would you like to continue anyway?",
            abort=True,
        )

    # Verify that the test plan that was generated has the correct
    # bypass/channel settings
    if (
        not race_test.test_config.network_manager_bypass
        or not race_test.test_config.comms_channel
        or not race_test.test_config.comms_channel_type
    ):
        raise error_utils.RIB603(
            race_test.export_plan_to_dict(),
            "Comms channel tests must have network_manager_bypass, comms_channel, comms_channel_type",
        )

    # Run the tests
    race_test.run_deployment_test(cli_context=cli_context)

    # Print the test report
    race_test.print_report()

    # If debug, going to create breakpoint for inspecting results
    if debug:
        breakpoint()

    # If `--raise-on-fail set and there are failures, raise exception
    if raise_on_fail and race_test.failed:
        raise error_utils.RIB601(deployment_name, race_test)


@test_command_group.command("generate-plan")
@deployment_name_option("test")
@pass_rib_mode
@run_time_option()
@is_running_option()
@delay_evaluation_option()
@delay_execute_option()
@delay_start_option()
@start_timeout_option()
@evaluation_interval_option()
@raise_on_fail_option()
@debug_option()
@click.option(
    "--comms-channel",
    "comms_channel",
    required=False,
    default=None,
    type=str,
    help="What channel to use with network-manager-bypass (focus of the test)",
)
@click.option(
    "--comms-channel-type",
    "comms_channel_type",
    required=False,
    default=None,
    type=click.Choice(["c2s", "s2s", "all"], case_sensitive=True),
    help="Type of channel",
)
@click.option(
    "--output-file",
    "output_file",
    required=False,
    default=None,
    type=str,
    help="Output File to Dump Plan",
)
@click.option(
    "--overwrite-file",
    "overwrite_file",
    flag_value=True,
    type=bool,
    help="Overwrite Test Plan File",
)
@click.option(
    "--raw",
    flag_value=True,
    help="Print raw, unescaped JSON",
    type=bool,
)
@click.pass_context
def generate_plan(
    cli_context: click.core.Context,
    deployment_name: str,
    rib_mode: str,
    run_time: int,
    is_running: bool,
    raise_on_fail: bool,
    delay_evaluation: int,
    delay_execute: int,
    delay_start: int,
    start_timeout: int,
    debug: bool,
    evaluation_interval: int,
    comms_channel: str,
    comms_channel_type: str,
    output_file: str,
    overwrite_file: bool,
    raw: bool,
):
    """
    Generate a test plan for future tests. Supports deployment + comms-channel
    """

    click.echo("Generating Test Plan File")

    # Getting instance of existing deployment
    deployment = RibDeployment.get_existing_deployment_or_fail(
        deployment_name, rib_mode
    )

    # Validate that the channel being tested is valid
    if comms_channel is not None and comms_channel not in [
        x["channel_name"] for x in deployment.comms_channels
    ]:
        raise error_utils.RIB602(deployment_name, comms_channel)

    # Generate the test plan (let utils decide the method)
    if comms_channel:
        race_test = RaceTest(
            deployment,
            run_time=run_time,
            delay_evaluation=delay_evaluation,
            delay_execute=delay_execute,
            delay_start=delay_start,
            start_timeout=start_timeout,
            evaluation_interval=evaluation_interval,
            is_running=is_running,
            comms_channel=comms_channel,
            comms_channel_type=comms_channel_type,
            network_manager_bypass=True,
        )
    else:
        race_test = RaceTest(
            deployment,
            run_time=run_time,
            delay_evaluation=delay_evaluation,
            delay_execute=delay_execute,
            delay_start=delay_start,
            start_timeout=start_timeout,
            evaluation_interval=evaluation_interval,
            is_running=is_running,
        )

    if raw:
        click.echo(general_utils.pretty_print_json(race_test.export_plan_to_dict()))
    else:
        click.echo(f"Escaped Test Plan: {race_test.export_plan_to_str()}")
    if output_file:
        race_test.export_plan_to_file(output_file, overwrite=overwrite_file)
        click.echo(f"Created Test Plan File: {output_file}")
