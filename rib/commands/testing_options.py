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
        Testing Command Group is responsible for running tests against RACE deployments
        and plugins
"""

# Python Library Imports
import click
from typing import Callable


###
# Common Args
###


def test_plan_file_option(
    command_help: str = "What Test Plan to Run? (Path to File relative to /code/ directory)",
):
    """
    Purpose:
        Custom option decorator for test plan file to read and execute
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @test_plan_file_option()
        def foo(test_plan_file: str):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--test-plan",
            "test_plan_file",
            required=False,
            type=str,
            default=None,
            help=command_help,
        )(function)

    return wrapper


def test_plan_json_option(
    command_help: str = "What Test Plan to Run? (Escaped JSON)",
):
    """
    Purpose:
        Custom option decorator for test plan to execute
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @test_plan_json_option()
        def foo(test_plan_json: str):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--test-plan-json",
            "test_plan_json",
            required=False,
            type=str,
            default=None,
            help=command_help,
        )(function)

    return wrapper


def run_time_option(
    command_help: str = "Time to allow test to run from (up to 86,400 seconds)",
) -> Callable:
    """
    Purpose:
        Custom option decorator for run time of the test
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @run_time_option()
        def foo(run_time: int):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--run-time",
            "run_time",
            type=click.IntRange(0, 86_400),
            default=120,
            required=False,
            help=command_help,
        )(function)

    return wrapper


def is_running_option(
    command_help: str = "Use an already running Deployment?",
):
    """
    Purpose:
        Custom option decorator for if we should use a running deployment for
        the test
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @is_running_option()
        def foo(is_running: bool):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--running",
            "is_running",
            flag_value=True,
            type=bool,
            help=command_help,
        )(function)

    return wrapper


def delay_evaluation_option(
    command_help: str = "Time (seconds) after starting test before running evaluation steps",
):
    """
    Purpose:
        Custom option decorator for how long to delay the evaluation after starting the test
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @delay_execute_option()
        def foo(delay_evaluation: int):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--delay-evaluation",
            type=click.IntRange(0, 3_600),
            default=30,
            required=False,
            help=command_help,
        )(function)

    return wrapper


def delay_execute_option(
    command_help: str = "Time (seconds) after starting nodes before running tests",
):
    """
    Purpose:
        Custom option decorator for how long to delay the test for things to
        start
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @delay_execute_option()
        def foo(delay_execute: int):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--delay-execute",
            type=click.IntRange(0, 3_600),
            default=15,
            required=False,
            help=command_help,
        )(function)

    return wrapper


def delay_start_option(
    command_help: str = "Time (seconds) after upping nodes before starting nodes",
):
    """
    Purpose:
        Custom option decorator for how long to delay the test for docker
        containers and external services to start (e.g. Butkus Gitlab)
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @delay_start_option()
        def foo(delay_start: int):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--delay-start",
            type=click.IntRange(0, 3_600),
            default=0,
            required=False,
            help=command_help,
        )(function)

    return wrapper


def evaluation_interval_option(
    command_help: str = "Time (seconds) to wait between attempts to validate test",
):
    """
    Purpose:
        Custom option decorator for how long to wait between attempting to validate the test
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @delay_execute_option()
        def foo(evaluation_interval: int):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--evaluation-interval",
            type=click.IntRange(0, 3_600),
            default=15,
            required=False,
            help=command_help,
        )(function)

    return wrapper


def start_timeout_option(
    command_help: str = "Time (seconds) to wait for nodes to start",
):
    """
    Purpose:
        Custom option decorator for how to wait for nodes to start
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @start_timeout_option()
        def foo(delay_start: int):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--start-timeout",
            type=click.IntRange(0, 3_600),
            default=300,
            required=False,
            help=command_help,
        )(function)

    return wrapper


def raise_on_fail_option(command_help: str = "Raise Exception on Failure?") -> Callable:
    """
    Purpose:
        Custom option decorator on whether or not to raise on failure
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @raise_on_fail_option()
        def foo(raise_on_fail: bool):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--raise-on-fail",
            "raise_on_fail",
            flag_value=True,
            type=bool,
            help=command_help,
        )(function)

    return wrapper


def debug_option(command_help: str = "Debug the test post run?") -> Callable:
    """
    Purpose:
        Custom option decorator for debugging test
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @debug_option()
        def foo(debug: bool):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--debug",
            "debug",
            flag_value=True,
            type=bool,
            help=command_help,
        )(function)

    return wrapper


def no_down_option(
    command_help: str = "Prevent the deployment from being downed to allow debugging the deployment?",
) -> Callable:
    """
    Purpose:
        Custom option decorator for controlling if the deployment is downed after the test
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @no_down_option()
        def foo(no_down: bool):
            pass
        ```

    """

    def wrapper(function):
        return click.option(
            "--no-down",
            "no_down",
            flag_value=True,
            type=bool,
            help=command_help,
        )(function)

    return wrapper
