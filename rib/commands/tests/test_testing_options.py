#!/usr/bin/env python3

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
        Test File for testing_options.py
"""

# Python Library Imports
import click
from click.testing import CliRunner
from typing import Callable

# Local Python Library Imports
from rib.commands import testing_options


###
# Helper Methods
###


def command_with_default_help(option_to_test: Callable) -> click.core.BaseCommand:
    """
    Purpose:
       Function wrapper for testing custom options with decorators
       in a way that is reusable and does not require copy/paste
    Args:
        option_to_test: the Click Option to test
    Returns:
        default_help: the option with default help
    """

    @click.command()
    @option_to_test()
    def default_help(*args, **kwargs) -> None:
        for kwarg, kwarg_value in kwargs.items():
            print(f"{kwarg}={kwarg_value}")

    return default_help


# def command_with_custom_help(option_to_test: Callable) -> Callable:
#     """
#     Purpose:
#        Function wrapper for testing custom options with decorators
#        in a way that is reusable and does not require copy/paste
#     Args:
#         option_to_test: the Click Option to test
#     Returns:
#         custom_help: the option with custom help
#     """

#     @click.command()
#     @testing_options.race_version_option(help="Custom Help")
#     def custom_help(race_version: str) -> None:
#         pass

# return custom_help


###
# Test Methods
###


def test_test_plan_file_option() -> int:
    """
    Test test_plan_file_option decorator for click commands
    """

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(
        command_with_default_help(testing_options.test_plan_file_option), []
    )
    assert result.exit_code == 0
    assert "test_plan_file=None" in result.output

    # When value is specified
    result = runner.invoke(
        command_with_default_help(testing_options.test_plan_file_option),
        ["--test-plan=x.json"],
    )
    assert result.exit_code == 0
    assert "test_plan_file=x.json" in result.output


def test_test_plan_json_option() -> int:
    """
    Test test_plan_json_option decorator for click commands
    """

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(
        command_with_default_help(testing_options.test_plan_json_option), []
    )
    assert result.exit_code == 0
    assert "test_plan_json=None" in result.output

    # When value is specified
    result = runner.invoke(
        command_with_default_help(testing_options.test_plan_json_option),
        ["--test-plan-json={}"],
    )
    assert result.exit_code == 0
    assert "test_plan_json={}" in result.output


def test_run_time_option() -> int:
    """
    Test run_time_option decorator for click commands
    """

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(
        command_with_default_help(testing_options.run_time_option), []
    )
    assert result.exit_code == 0
    assert "run_time=120" in result.output

    # When value is specified
    result = runner.invoke(
        command_with_default_help(testing_options.run_time_option),
        ["--run-time=3"],
    )
    assert result.exit_code == 0
    assert "run_time=3" in result.output


def test_is_running_option() -> int:
    """
    Test is_running_option decorator for click commands
    """

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(
        command_with_default_help(testing_options.is_running_option), []
    )
    assert result.exit_code == 0
    assert "is_running=False" in result.output

    # When value is specified
    result = runner.invoke(
        command_with_default_help(testing_options.is_running_option),
        ["--running"],
    )
    assert result.exit_code == 0
    assert "is_running=True" in result.output


def delay_execute_option() -> int:
    """
    Test delay_execute_option decorator for click commands
    """

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(
        command_with_default_help(testing_options.delay_execute_option), []
    )
    assert result.exit_code == 0
    assert "delay_execute=15" in result.output

    # When value is specified
    result = runner.invoke(
        command_with_default_help(testing_options.delay_execute_option),
        ["--delay-execute=30"],
    )
    assert result.exit_code == 0
    assert "delay_execute=30" in result.output


def delay_start_option() -> int:
    """
    Test delay_start_option decorator for click commands
    """

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(
        command_with_default_help(testing_options.delay_start_option), []
    )
    assert result.exit_code == 0
    assert "delay_start=0" in result.output

    # When value is specified
    result = runner.invoke(
        command_with_default_help(testing_options.delay_start_option),
        ["--delay-start=30"],
    )
    assert result.exit_code == 0
    assert "delay_start=30" in result.output


def test_raise_on_fail_option() -> int:
    """
    Test raise_on_fail_option decorator for click commands
    """

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(
        command_with_default_help(testing_options.raise_on_fail_option), []
    )
    assert result.exit_code == 0
    assert "raise_on_fail=False" in result.output

    # When value is specified
    result = runner.invoke(
        command_with_default_help(testing_options.raise_on_fail_option),
        ["--raise-on-fail"],
    )
    assert result.exit_code == 0
    assert "raise_on_fail=True" in result.output


def test_debug_option() -> int:
    """
    Test debug_option decorator for click commands
    """

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(command_with_default_help(testing_options.debug_option), [])
    assert result.exit_code == 0
    assert "debug=False" in result.output

    # When value is specified
    result = runner.invoke(
        command_with_default_help(testing_options.debug_option),
        ["--debug"],
    )
    assert result.exit_code == 0
    assert "debug=True" in result.output
