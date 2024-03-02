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
        Utilities for Working with Click
"""

# Python Library Imports
import click.testing

# from click.testing import CliRunner
from typing import Any, Callable, Dict, List, Optional

# Local Python Library Imports
# N/A


###
# Click Arg Functions
###


def get_click_arguments(
    command_args: Optional[List[str]] = None,
    command_kwargs: Optional[Dict[str, Any]] = None,
    command_flags: Optional[List[str]] = None,
) -> List[str]:
    """
    Purpose:
        Parse Args, Kwargs, and Flags into List for Click
    Args:
        command_args (List): List of args to pass to the command
        command_kwargs (Dict): Dict of kwargs to pass to the command
        command_flags (List): List of flags to pass to the command
    Returns:
        click_command_args (List): Parsed List of args to pass to the command
    """

    click_command_args = []

    # Add specific arguments to the list of arguments
    if command_args:
        for arg in command_args:
            click_command_args.append(arg)
    if command_kwargs:
        for kwarg, value in command_kwargs.items():
            click_command_args.append(kwarg)
            click_command_args.append(value)
    if command_flags:
        for flag in command_flags:
            click_command_args.append(flag)

    return click_command_args


###
# Click Wrapping Functions
###


def call_click_command(
    command: Callable, context_obj: object, arguments: List[Any]
) -> object:
    """
    Purpose:
        Make a call to a click command with specified arguments. Use
        a specified context_obj, which is an instance of the RaceInTheBoxState
        Class.
    Args:
        command (function): Click function to call
        context_obj (RaceInTheBoxState Obj): State of RiB Object
        arguments (List): List of arguments to send to click.
            Note: if kwarg, looks like ["--name", "{value}"]
            if arg, looks like ["{value}"]
    Returns:
        command_result (Click Command Obj): Result of the command, has output
            , exception, etc
    """

    click_runner = click.testing.CliRunner()
    command_result = click_runner.invoke(
        command,
        args=arguments,
        input=None,
        env=None,
        obj=context_obj,
        catch_exceptions=True,
    )

    return command_result


###
# Click Info Functions
###


def get_run_command(current_command: object) -> str:
    """
    Purpose:
        Get a stringified command that was run using Clicks context object
    Args:
        current_command (Click Context Obj: Obj holding Click state and history
    Returns:
        run_command (String): Command the user ran
    """

    command_path = current_command.command_path
    run_commands = []

    while current_command:
        # Get Command Info, parse to find what options result in variables
        # command_options = current_command.command.opts
        command_name = current_command.info_name

        command_params = {
            command_param.name: command_param.opts[0]
            for command_param in current_command.command.params
        }

        count_params = [
            param.name for param in current_command.command.params if param.count
        ]

        # Get Passed In Info
        args = current_command.args
        params_raw = current_command.params

        # Parse args and params to get command
        args_str = " ".join(args)
        params = []

        for param, value in params_raw.items():
            # Ignore Null/Optional values
            if not value:
                continue

            # Set counted params as repeated flags
            elif param in count_params:
                for _ in range(int(value)):
                    params.append(command_params.get(param, "--unknown"))

            # Set bools as flags
            elif isinstance(value, bool):
                params.append(f"{command_params.get(param, '--unknown')}")

            # Lists/Tuples are multi options
            elif isinstance(value, (list, tuple)):
                for list_value in value:
                    params.append(
                        f"{command_params.get(param, '--unknown')}={list_value}"
                    )

            # Set everything else as an option
            else:
                params.append(f"{command_params.get(param, '--unknown')}={value}")

        params_str = " ".join(params)

        run_commands.insert(0, f"{command_name} {args_str} {params_str}".strip())

        # Return
        current_command = current_command.parent

    return " ".join(run_commands)
