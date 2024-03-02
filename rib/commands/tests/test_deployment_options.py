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
        Test File for deployment_options.py
"""

# Python Library Imports
import click
from click.testing import CliRunner
from typing import Any, Callable, Dict
from unittest.mock import patch

# Local Python Library Imports
from rib.commands import deployment_options


###
# Helper Methods
###


def command_with_default_help(
    option_to_test: Callable, **option_args: Dict[str, Any]
) -> click.core.BaseCommand:
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
    @option_to_test("test", **option_args)
    def default_help(*args, **kwargs) -> None:
        for kwarg, kwarg_value in kwargs.items():
            print(f"{kwarg}={kwarg_value}")

    return default_help


###
# Test Methods
###


#########
# warn_if_in_name
#########


def test_warn_if_in_name_linux_server() -> int:
    """
    Purpose:
        Check `warn_if_in_name()` works for linux-server
    Args:
        N/A
    """

    with patch("click.secho") as secho_mock, patch("click.confirm") as confirm_mock:
        confirm_mock.return_value = True
        deployment_options._warn_if_in_name(
            name="some_server_image",
            image_type="Linux server",
            words=["client", "android"],
        )

        assert secho_mock.call_count == 0
        assert confirm_mock.call_count == 0

    with patch("click.secho") as secho_mock, patch("click.confirm") as confirm_mock:
        confirm_mock.return_value = True
        deployment_options._warn_if_in_name(
            name="some_client_image",
            image_type="Linux server",
            words=["client", "android"],
        )

        assert secho_mock.call_count == 1
        assert confirm_mock.call_count == 1

    with patch("click.secho") as secho_mock, patch("click.confirm") as confirm_mock:
        confirm_mock.return_value = True
        deployment_options._warn_if_in_name(
            name="some_android_image",
            image_type="Linux server",
            words=["client", "android"],
        )

        assert secho_mock.call_count == 1
        assert confirm_mock.call_count == 1


def test_warn_if_in_name_linux_server() -> int:
    """
    Purpose:
        Check `warn_if_in_name()` works for linux-client
    Args:
        N/A
    """

    with patch("click.secho") as secho_mock, patch("click.confirm") as confirm_mock:
        confirm_mock.return_value = True
        deployment_options._warn_if_in_name(
            name="some_server_image",
            image_type="Linux client",
            words=["server", "android"],
        )

        assert secho_mock.call_count == 1
        assert confirm_mock.call_count == 1

    with patch("click.secho") as secho_mock, patch("click.confirm") as confirm_mock:
        confirm_mock.return_value = True
        deployment_options._warn_if_in_name(
            name="some_client_image",
            image_type="Linux client",
            words=["server", "android"],
        )

        assert secho_mock.call_count == 0
        assert confirm_mock.call_count == 0

    with patch("click.secho") as secho_mock, patch("click.confirm") as confirm_mock:
        confirm_mock.return_value = True
        deployment_options._warn_if_in_name(
            name="some_android_image",
            image_type="Linux client",
            words=["server", "android"],
        )

        assert secho_mock.call_count == 1
        assert confirm_mock.call_count == 1


def test_warn_if_in_name_linux_server() -> int:
    """
    Purpose:
        Check `warn_if_in_name()` works for android-client
    Args:
        N/A
    """

    with patch("click.secho") as secho_mock, patch("click.confirm") as confirm_mock:
        confirm_mock.return_value = True
        deployment_options._warn_if_in_name(
            name="some_server_image",
            image_type="Android client",
            words=["server", "linux"],
        )

        assert secho_mock.call_count == 1
        assert confirm_mock.call_count == 1

    with patch("click.secho") as secho_mock, patch("click.confirm") as confirm_mock:
        confirm_mock.return_value = True
        deployment_options._warn_if_in_name(
            name="some_linux_image",
            image_type="Android client",
            words=["server", "linux"],
        )

        assert secho_mock.call_count == 1
        assert confirm_mock.call_count == 1

    with patch("click.secho") as secho_mock, patch("click.confirm") as confirm_mock:
        confirm_mock.return_value = True
        deployment_options._warn_if_in_name(
            name="some_android_image",
            image_type="Android client",
            words=["server", "linux"],
        )

        assert secho_mock.call_count == 0
        assert confirm_mock.call_count == 0


#########
# warn_if_invalid_docker_image
#########


def test_warn_if_invalid_docker_image_valid() -> int:
    """
    Purpose:
        Check `warn_if_invalid_docker_image()` works when image is valid
    Args:
        N/A
    """

    with patch("click.secho") as secho_mock, patch(
        "click.confirm"
    ) as confirm_mock, patch(
        "rib.utils.docker_utils.validate_docker_image_name"
    ) as validate_mock:
        validate_mock.return_value = True
        confirm_mock.return_value = True
        deployment_options._warn_if_invalid_docker_image("some_value")

        assert validate_mock.call_count == 1
        assert secho_mock.call_count == 0
        assert confirm_mock.call_count == 0


def test_warn_if_invalid_docker_image_invalid() -> int:
    """
    Purpose:
        Check `warn_if_invalid_docker_image()` works when image is invalid
    Args:
        N/A
    """

    with patch("click.secho") as secho_mock, patch(
        "click.confirm"
    ) as confirm_mock, patch(
        "rib.utils.docker_utils.validate_docker_image_name"
    ) as validate_mock:
        validate_mock.return_value = False
        confirm_mock.return_value = True
        deployment_options._warn_if_invalid_docker_image("some_value")

        assert validate_mock.call_count == 1
        assert secho_mock.call_count == 1
        assert confirm_mock.call_count == 1


###
# deployment_name_option
###


def test_deployment_name_option() -> int:
    """
    Test deployment_name_option decorator for click commands
    """

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(
        command_with_default_help(deployment_options.deployment_name_option), []
    )
    assert result.exit_code == 2
    assert "Missing option '--name'" in result.output

    # When value is specified
    result = runner.invoke(
        command_with_default_help(deployment_options.deployment_name_option),
        ["--name=test"],
    )
    assert "Using default" not in result.output
    assert "deployment_name=test" in result.output


def test_deployment_name_rejects_canned_prefix() -> int:
    runner = CliRunner()
    result = runner.invoke(
        command_with_default_help(
            deployment_options.deployment_name_option, validate=True
        ),
        ["--name=canned-test"],
    )
    assert result.exit_code == 2
    assert 'Name cannot start with "canned' in result.output


def test_deployment_name_rejects_non_path() -> int:
    runner = CliRunner()
    result = runner.invoke(
        command_with_default_help(
            deployment_options.deployment_name_option, validate=True
        ),
        ["--name=!@#$%^&U*/\\[]("],
    )
    assert result.exit_code == 2
    assert "Name contains invalid characters" in result.output
