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
    Custom decorators to standardize click options
"""

# Python Library Imports
from enum import Enum
import click
import logging
from datetime import datetime
from typing import Any, Callable, Optional

# Local Python Library Imports
from rib.utils import plugin_utils, rib_utils


logger = logging.getLogger(__name__)

RIB_CONFIG = rib_utils.load_race_global_configs()
DEFAULT_RACE_VERSION = "2.4.*"


###
# Global config default options
###


def default_from_context(
    name: str, get_default_from_ctx: Callable[[click.Context], Any]
) -> click.Option:
    """
    Purpose:
        Creates a custom option type to use as the base class for a click option
    Args:
        name: Name of the option
        get_default_from_ctx: Callable invoked to obtain the default value from context
    Returns:
        Customized click option type with dynamic default value
    Example:
        @click.option(cls=default_from_context("my value", lambda ctx : ctx.obj.default_value))
    """

    class OptionDefaultFromContext(click.Option):
        """Customized click option with dynamic default value"""

        def get_default(self, ctx, call=True, **kwargs):
            """
            Purpose:
                Obtain the default value for the option
            Args:
                ctx: Click context
                call: Will be False if invoked as part of a help command
            Return:
                Default value
            """
            self.default = get_default_from_ctx(ctx)
            if call:
                click.echo(f"Using default {name}: {self.default}")
            return super().get_default(ctx)

    return OptionDefaultFromContext


def use_default_value(name: str, value: Any) -> Callable[[], Any]:
    """
    Purpose:
        Create a callable to print a message about using a default value and then return
        the default value
    Args:
        name: Name of the option
        value: Default value of the option
    Return:
        Callable that returns the default value
    """

    def use_default_func():
        logger.info(f"Using default {name}: {value}")
        return value

    return use_default_func


def race_version_option(
    command_help: str = "What version of RACE", group: click.Group = click
):
    """
    Purpose:
        Custom option decorator for the RACE version.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @race_version_option(help="What version of RACE to use")
        def foo(race_version: str):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--race",
            "race_version",
            type=str,
            help=command_help,
            default=use_default_value("RACE version", DEFAULT_RACE_VERSION),
            show_default=DEFAULT_RACE_VERSION,
        )(function)

    return wrapper


def rib_mode_option(
    command_help: str = "What mode are you running RiB in? (local or aws)",
):
    """
    Purpose:
        Custom option decorator for the RiB mode.
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @rib_mode_option()
        def foo(rib_mode: str):
            pass
        ```
    """

    def wrapper(function):
        get_default_from_ctx = lambda ctx: ctx.obj.rib_mode or "local"
        return click.option(
            "--mode",
            "rib_mode",
            cls=default_from_context("RiB mode", get_default_from_ctx),
            type=click.Choice(["local", "aws"], case_sensitive=False),
            help=command_help,
            show_default=True,
        )(function)

    return wrapper


def detail_level_option(command_help: str = "Increase level of details in output"):
    """
    Purpose:
        Custom option decorator for the detail level.
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @detail_level_option()
        def foo(detail_level: int):
            pass
        ```
    """

    def wrapper(function):
        get_default_from_ctx = lambda ctx: ctx.obj.detail_level or 0
        return click.option(
            "-d",
            "detail_level",
            cls=default_from_context("detail level", get_default_from_ctx),
            count=True,
            help=command_help,
            show_default=True,
        )(function)

    return wrapper


def verbosity_option(command_help: str = "Increase verbosity of output"):
    """
    Purpose:
        Custom option decorator for the verbosity level.
    Args:
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @verbosity_option()
        def foo(verbosity: int):
            pass
        ```
    """

    def wrapper(function):
        get_default_from_ctx = lambda ctx: ctx.obj.verbosity or 0
        return click.option(
            "-V",  # Renamed from "-v" to avoid conflict with global logging verbosity option
            "--verbosity",
            cls=default_from_context("verbosity", get_default_from_ctx),
            count=True,
            help=command_help,
            show_default=True,
        )(function)

    return wrapper


def timeout_option(
    command_help: str = "Timeout for operation (in seconds)",
    default: int = 120,
):
    """
    Purpose:
        Custom option decorator to specify the operation timeout
    Args:
        command_help: Help description
        default: Default timeout value
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @timeout_option()
        def foo(timeout: int):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--timeout",
            type=click.IntRange(0, 3_600_000),
            default=default,
            required=False,
            show_default=True,
            help=command_help,
        )(function)

    return wrapper


def dry_run_option(
    command_help: str = "Perform dry-run of the operation",
    hidden: bool = True,
):
    """
    Purpose:
        Custom option decorator to specify a dry-run flag
    Args:
        command_help: Help description
        hidden: Hide option from the help menu
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @dry_run_option()
        def foo(dry_run: bool):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--dry-run",
            flag_value=True,
            help=command_help,
            hidden=hidden,
        )(function)

    return wrapper


def format_option(
    command_help="Format output as JSON or YAML",
    default=None,
    required=False,
):
    """
    Purpose:
        Custom option decorator to specify an output format option
    Args:
        command_help: Help description
        default: Default format option
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @format_option()
        def foo(format: Optional[str]):
            pass
    """

    def wrapper(function):
        return click.option(
            "--format",
            default=default,
            help=command_help,
            required=required,
            type=click.Choice(["json", "yaml"]),
        )(function)

    return wrapper


def ansible_verbosity_option(
    command_help: str = "Ansible output verbosity",
    default: int = 2,
    hidden: bool = True,
):
    """
    Purpose:
        Custom option decorator for the ansible verbosity level.
    Args:
        command_help: Help description
        default: Default verbosity level
        hidden: Hide option from the help menu
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @ansible_verbosity_option()
        def foo(ansible_verbosity: int):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--ansible-verbosity",
            default=default,
            help=command_help,
            hidden=hidden,
            type=int,
        )(function)

    return wrapper


def out_option(
    command_help: str = "Output file",
    default: Optional[str] = None,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for an output file.
    Args:
        command_help: Help description
        default: Default out file
        required: Whether the option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @out_option()
        def foo(out: Optional[str]):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--out",
            default=default,
            help=command_help,
            required=required,
            show_default=True,
            type=str,
        )(function)

    return wrapper


###
# Enum options
###


class EnumParamType(click.Choice):
    """Specialization of Choice parameters for enums"""

    def __init__(self, enum: Enum, case_sensitive: bool = False):
        self._enum = enum
        super().__init__(
            choices=[item.name for item in enum], case_sensitive=case_sensitive
        )

    def convert(
        self, value: Any, param: Optional[click.Parameter], ctx: click.Context
    ) -> Optional[Enum]:
        """
        Purpose:
            Convert the string value from Choice into an Enum
        Args:
            value: Parameter value
            param: Click parameter
            ctx: Click context
        Return:
            None or Enum value
        """
        if value is None or isinstance(value, Enum):
            return value

        converted = super().convert(value, param, ctx)
        return self._enum[converted]


def cache_option(
    default: plugin_utils.CacheStrategy = plugin_utils.CacheStrategy.AUTO,
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator to specify the artifact caching strategy
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @cache_option()
        def foo(cache: plugin_utils.CacheStrategy):
            pass
        ```
    """

    command_help = (
        "Whether to use locally-cached artifacts:"
        "\n\n never: re-download the artifact every time, even if it is already cached"
        "\n\n always: use cached copy if it exists, else download into the cache"
        "\n\n auto: force a re-download if using the latest revision, else use cached copy if it exists"
    )

    def wrapper(function):
        return group.option(
            "--cache",
            default=default.name,
            help=command_help,
            type=EnumParamType(plugin_utils.CacheStrategy),
        )(function)

    return wrapper


def generate_timestamp() -> str:
    """
    Purpose:
        Generates a timestamp based on the current time.
    Returns:
        Auto-generated timestamp based on current time.
    """
    return datetime.now().astimezone().strftime("%Y%m%dT%H%M%S%Z")
