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
    Custom decorators to standardize click options for deployment commands
"""

# Python Library Imports
import click
import functools
import logging
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional

# Local Python Library Imports
from rib.commands.common_options import use_default_value
from rib.utils import docker_utils, github_utils, plugin_utils


logger = logging.getLogger(__name__)


###
# Defaults
###


def use_default_image(image_type: str, image: str):
    """
    Purpose:
        Create a default function for an image option
    Args:
        image_type: What type of image is the option for
        image: The default image name
    Return:
        Callable that returns the default image value
    """

    def use_default_func():
        value = github_utils.default_image(image)
        logger.info(f"Using default {image_type} image: {value}")
        return value

    return use_default_func


###
# Callback/validation
###


def _ensure_unique(context: click.Context, param: click.Parameter, value: Any) -> Any:
    """Ensure a multiple option has unique values defined"""
    if isinstance(value, tuple):
        if len(value) != len(set(value)):
            raise click.BadParameter("Duplicate values given")
    return value


def _expand_image(image: str):
    """Expand the image name to the full image name using defaults if only a name or tag was provided"""

    def callback_func(
        context: click.Context, param: click.Parameter, value: Any
    ) -> Any:
        if value is not None:
            return github_utils.apply_defaults_to_image(value, image)
        return None

    return callback_func


def _parse_kit_source(
    context: click.Context, param: click.Parameter, value: Any
) -> plugin_utils.KitSource:
    if value is not None:
        source = plugin_utils.parse_kit_source(value)
        return plugin_utils.apply_kit_defaults(source)
    return None


def _parse_kit_sources(
    context: click.Context, param: click.Parameter, value: Any
) -> List[plugin_utils.KitSource]:
    if value is not None:
        sources = []
        for val in value:
            source = plugin_utils.parse_kit_source(val)
            source = plugin_utils.apply_kit_defaults(source)
            sources.append(source)
        return sources
    return None


###
# Command decorators
###


def pass_rib_mode(func: Callable) -> Callable:
    """
    Purpose:
        Custom command decorator to receive the appropriate deployment mode as an argument
    Args:
        func: Click command function
    Returns:
        Decorator
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        rib_mode = click.get_current_context().obj.rib_mode
        return func(*args, **kwargs, rib_mode=rib_mode)

    return wrapper


# TODO remove this
def pass_default_artifact_revisions(func: Callable) -> Callable:
    """
    Purpose:
        Custom command decorator to set missing artifact revision arguments using the env option
        value
    Args:
        func: Click command function
    Returns:
        Decorator
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def _warn_if_in_name(name: str, image_type: str, words: List[str]):
    """
    Purpose:
        Checks if any of the given "bad" words exist in the given image name. If found,
        a warning is printed (e.g., if the user specified "my_android_client_image" as the
        Linux server image by mistake).
    Args:
        name: Image name (may be None)
        type: Image type (e.g., Android client, Linux server)
        words: List of words to look for in the image name
    """
    name = name.lower() if name else ""
    for word in words:
        if word.lower() in name:
            click.secho(
                f"WARNING: {image_type} image name contains the word '{word}'. "
                "Was this intentional?",
                fg="red",
            )
            click.confirm("Would you like to continue?", abort=True)


def _warn_if_invalid_docker_image(docker_image: str) -> None:
    """
    Purpose:
        Checks if provided docker images a are "bad". warns (doesn't fail)
        at the moment to make sure we are not missing something. will become blocking
        in a fugure release
    Args:
        name: Image name (may be None)
        type: Image type (e.g., Android client, Linux server)
        words: List of words to look for in the image name
    """

    if not docker_utils.validate_docker_image_name(docker_image):
        click.secho(
            f"WARNING: Provided Docker Image {docker_image} contains invalid "
            "characters.",
            fg="red",
        )
        click.confirm("Would you like to continue?", abort=True)


def validate_image_names(func: Callable) -> Callable:
    """
    Purpose:
        Custom command decorator to validate RACE node image _names_ (does not check if the image
        actually exists)
    Args:
        func: Click command function
    Returns:
        Decorator
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        android_client_image = kwargs.get("android_client_image")
        if android_client_image:
            _warn_if_in_name(
                name=android_client_image,
                image_type="Android client",
                words=["server", "linux"],
            )
            _warn_if_invalid_docker_image(android_client_image)

        linux_client_image = kwargs.get("linux_client_image")
        if linux_client_image:
            _warn_if_in_name(
                name=linux_client_image,
                image_type="Linux client",
                words=["server", "android"],
            )
            _warn_if_invalid_docker_image(linux_client_image)
            if linux_client_image == android_client_image:
                click.secho(
                    f"WARNING: same image provided for both Android client and Linux client",
                    fg="red",
                )

        linux_server_image = kwargs.get("linux_server_image")
        if linux_server_image:
            _warn_if_in_name(
                name=linux_server_image,
                image_type="Linux server",
                words=["client", "android"],
            )
            _warn_if_invalid_docker_image(linux_server_image)
            if linux_server_image == android_client_image:
                click.secho(
                    f"WARNING: same image provided for both Android client and Linux server",
                    fg="red",
                )

        return func(*args, **kwargs)

    return wrapper


###
# Option decorators
###


def android_app_option(
    command_help: str = "Android RACE app to use",
    default: str = "core=raceclient-android",
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the Android app source.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @android_app_option()
        def foo(android_app: plugin_utils.KitSource):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--android-app",
            callback=_parse_kit_source,
            default=use_default_value("Android app", default),
            help=command_help,
            required=required,
            type=str,
        )(function)

    return wrapper


def android_client_count_option(
    command_help: str = "Number of Android clients", group: click.Group = click
):
    """
    Purpose:
        Custom option decorator for the android client count option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @android_client_count_option()
        def foo(android_client_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--android-client-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def android_client_image_option(
    command_help="Docker image to use for Android client containers",
    default="race-runtime-android-x86_64",
    group: click.Group = click,
    hidden=False,
    required=False,
):
    """
    Purpose:
        Custom option decorator for the android client image option.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        hidden: if Option is hidden
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @android_client_image_option()
        def foo(android_client_image: str):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--android-client-image",
            callback=_expand_image(default),
            default=use_default_image("Android client", default),
            help=command_help,
            hidden=hidden,
            required=required,
            type=str,
        )(function)

    return wrapper


def android_client_uninstalled_count_option(
    command_help: str = "Number of Android clients without RACE installed",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the android client uninstalled count option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @android_client_uninstalled_count_option()
        def foo(android_client_uninstalled_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--android-client-uninstalled-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def android_client_bridge_count_option(
    command_help: str = "Number of Android clients to be bridged into the deployment",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the android client bridge count option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @android_client_bridge_count_option()
        def foo(android_client_bridge_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--android-client-bridge-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def artifact_manager_kits_option(
    command_help: str = "Artifact manager kits to use",
    default: Iterable[str] = (
        # Order is important here
        "core=plugin-artifact-manager-twosix-cpp-local",
        "core=plugin-artifact-manager-twosix-cpp",
    ),
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the artifact manager kit sources.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @artifact_manager_kits_option()
        def foo(artifact_manager_kits: List[plugin_utils.KitSource]):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--artifact-manager-kit",
            "artifact_manager_kits",
            callback=_parse_kit_sources,
            default=use_default_value("Artifact manager kits", default),
            help=command_help,
            multiple=True,
            required=required,
            type=str,
        )(function)

    return wrapper


def bastion_image_option(
    command_help="Docker image to use for the bastion container",
    default="race-bastion",
    group: click.Group = click,
    hidden=False,
    required=False,
):
    """
    Purpose:
        Custom option decorator for the bastion image option.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        hidden: if Option is hidden
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @bastion_image_option()
        def foo(bastion_image: str):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--bastion-image",
            callback=_expand_image(default),
            default=use_default_image("Bastion", default),
            help=command_help,
            hidden=hidden,
            required=required,
            type=str,
        )(function)

    return wrapper


def bastion_ip_option(
    flag: Optional[bool] = None,
    command_help: str = "IP address of the bastion server to use with the deployment",
):
    """
    Purpose:
        Custom option decorator for the bastion IP option.
    Args:
        flag: Use option as a switch flag rather than a value option
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @bastion_ip_option()
        def foo(bastion_ip: str):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--bastion",
            "bastion_ip",
            default=None,
            flag_value=flag,
            help=command_help,
            required=False,
            type=str,
        )(function)

    return wrapper


def _validate_deployment_name(
    context: click.Context, param: click.Parameter, value: Any
) -> str:
    """Ensure that deployment name contains only allowed characters"""
    if value.startswith("canned"):
        raise click.BadParameter('Name cannot start with "canned"; names are reserved')

    # Check that name will be a valid directory name
    if len(value) != len(Path(value).name):
        raise click.BadParameter("Name contains invalid characters")

    return value


def deployment_name_option(action: str, validate: bool = False):
    """
    Purpose:
        Custom option decorator for the deployment name option.
    Args:
        action: Deployment action
        validate: Whether to validate the name value
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @deployment_name_option("start")
        def foo(deployment_name: str):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--name",
            "deployment_name",
            callback=_validate_deployment_name if validate else None,
            envvar="DEPLOYMENT_NAME",
            help=f"What deployment to {action}?",
            required=True,
            type=str,
        )(function)

    return wrapper


def artifact_env_option(
    command_help: str = "Set env for default artifact revisions (plugins, images, etc.)",
    group: click.Group = click,
    hidden: bool = True,
):
    """
    Purpose:
        Custom option decorator for the artifact env option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @artifact_env_option()
        def foo(artifact_env: str):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--env",
            "artifact_env",
            default="prod",
            help=command_help,
            hidden=hidden,
            type=click.Choice(["dev", "prod"]),
        )(function)

    return wrapper


def disabled_channels_option(
    command_help: str = "Channels to be initially disabled on first application start",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for disabled channel names configuration option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @disabled_channels_option("create")
        def foo(disabled_channels: Optional[List[str]]):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--disabled-channel",
            "disabled_channels",
            multiple=True,
            required=False,
            type=str,
            default=None,
            help=command_help,
        )(function)

    return wrapper


def enable_ui_option(
    command_help: str = "Nodes for which to enable user input UI",
    group: click.Group = click,
    param: str = "--enable-ui",
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the node names for which to enable the user input UI.
    Args:
        command_help: Help description
        group: Optional parent group
        param: Flag for the option
        required: Option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @enable_ui_option()
        def foo(enable_ui: Optional[List[str]]):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            param,
            multiple=True,
            required=required,
            type=str,
            default=None,
            help=command_help,
        )(function)

    return wrapper


def fetch_plugins_on_start_option(
    command_help: str = "Enable fetching of plugins from artifact managers on application start",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the fetch-plugins-on-start configuration option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @fetch_plugins_on_start_option()
        def foo(fetch_plugins_on_start: bool):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--fetch-plugins-on-start",
            flag_value=True,
            help=command_help,
        )(function)

    return wrapper


def linux_app_option(
    command_help: str = "Linux RACE app to use",
    default: str = "core=racetestapp-linux",
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the Linux app source.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_app_option()
        def foo(linux_app: plugin_utils.KitSource):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-app",
            callback=_parse_kit_source,
            default=use_default_value("Linux app", default),
            help=command_help,
            required=required,
            type=str,
        )(function)

    return wrapper


def registry_app_option(
    command_help: str = "Registry app to use",
    default: str = None,
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the Registry app source.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @registry_app_option()
        def foo(registry_app: plugin_utils.KitSource):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--registry-app",
            callback=_parse_kit_source,
            default=use_default_value("Registry app", default) if default else None,
            help=command_help,
            required=required,
            type=str,
        )(function)

    return wrapper


def node_daemon_option(
    command_help: str = "RACE node daemon to use",
    default: str = "core=race-node-daemon",
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the node daemon source.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @node_daemon_option()
        def foo(node_daemon: plugin_utils.KitSource):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--node-daemon",
            callback=_parse_kit_source,
            default=use_default_value("Node daemon", default),
            help=command_help,
            required=required,
            type=str,
        )(function)

    return wrapper


def linux_client_count_option(
    command_help: str = "Number of Linux clients", group: click.Group = click
):
    """
    Purpose:
        Custom option decorator for the linux client count option.
    Args:
        command_help: Help description
        click: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_client_count_option()
        def foo(linux_client_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-client-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def linux_client_image_option(
    command_help="Docker image to use for Linux client containers",
    default="race-runtime-linux",
    group: click.Group = click,
    hidden=False,
    required=False,
):
    """
    Purpose:
        Custom option decorator for the Linux client image option.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        hidden: if Option is hidden
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_client_image_option()
        def foo(linux_client_image: str):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-client-image",
            callback=_expand_image(default),
            default=use_default_image("Linux client", default),
            help=command_help,
            hidden=hidden,
            required=required,
            type=str,
        )(function)

    return wrapper


def linux_client_uninstalled_count_option(
    command_help: str = "Number of Linux clients without RACE installed",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the linux client uninstalled count option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_client_uninstalled_count_option()
        def foo(linux_client_uninstalled_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-client-uninstalled-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def linux_client_bridge_count_option(
    command_help: str = "Number of Linux clients to be bridged into the deployment",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the linux client bridge count option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_client_bridge_count_option()
        def foo(linux_client_bridge_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-client-bridge-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def linux_gpu_client_count_option(
    command_help: str = "Number of Linux clients with GPU support",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the linux GPU client count option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_gpu_client_count_option()
        def foo(linux_gpu_client_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-gpu-client-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def linux_gpu_server_count_option(
    command_help: str = "Number of Linux servers with GPU support",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the linux GPU server count option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_gpu_server_count_option()
        def foo(linux_gpu_server_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-gpu-server-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def linux_server_count_option(
    command_help: str = "Number of Linux servers",
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the linux server count option.
    Args:
        command_help: Help description
        group: Optional parent group
        required: Argument is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_server_count_option()
        def foo(linux_server_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-server-count",
            default=0,
            help=command_help,
            required=required,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def linux_server_image_option(
    command_help="Docker image to use for Linux server containers",
    default="race-runtime-linux",
    group: click.Group = click,
    hidden=False,
    required=False,
):
    """
    Purpose:
        Custom option decorator for the Linux server image option.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        hidden: if Option is hidden
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_server_image_option()
        def foo(linux_server_image: str):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-server-image",
            callback=_expand_image(default),
            default=use_default_image("Linux server", default),
            help=command_help,
            hidden=hidden,
            required=required,
            type=str,
        )(function)

    return wrapper


def linux_server_uninstalled_count_option(
    command_help: str = "Number of Linux servers without RACE installed",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the linux server uninstalled count option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_server_uninstalled_count_option()
        def foo(linux_server_uninstalled_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-server-uninstalled-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def linux_server_bridge_count_option(
    command_help: str = "Number of Linux servers to be bridged into the deployment",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the linux server bridge count option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @linux_server_bridge_count_option()
        def foo(linux_server_bridge_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--linux-server-bridge-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def registry_client_count_option(
    command_help: str = "Number of Registry clients", group: click.Group = click
):
    """
    Purpose:
        Custom option decorator for the registry client count option.
    Args:
        command_help: Help description
        click: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @registry_client_count_option()
        def foo(registry_client_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--registry-client-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def registry_client_uninstalled_count_option(
    command_help: str = "Number of Registry Clients without RACE installed",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the registry client uninstalled count option.
    Args:
        command_help: Help description
        click: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @registry_client_uninstalled_count_option()
        def foo(registry_client_uninstalled_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--registry-client-uninstalled-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def gpu_registry_client_count_option(
    command_help: str = "Number of Registry Clients with GPU support",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the registry GPU client count option.
    Args:
        command_help: Help description
        click: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @gpu_registry_client_count_option()
        def foo(gpu_registry_client_count: int):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--gpu-registry-client-count",
            default=0,
            help=command_help,
            required=False,
            show_default=True,
            type=click.IntRange(min=0),
        )(function)

    return wrapper


def registry_client_image_option(
    command_help="Docker image to use for registry client containers",
    default="race-runtime-linux",
    group: click.Group = click,
    hidden=False,
    required=False,
):
    """
    Purpose:
        Custom option decorator for the registry client image option.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        hidden: if Option is hidden
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @registry_client_image_option()
        def foo(registry_client_image: str):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--registry-client-image",
            callback=_expand_image(default),
            default=use_default_image("Registry client", default),
            help=command_help,
            hidden=hidden,
            required=required,
            type=str,
        )(function)

    return wrapper


def no_config_gen_option(
    command_help: str = "Prevent default config generation from running",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for the no-config-gen option.
    Args:
        command_help: Help description
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @no_config_gen_option()
        def foo(no_config_gen: bool):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--no-config-gen",
            flag_value=True,
            help=command_help,
        )(function)

    return wrapper


def nodes_option(action: str, required: bool = False):
    """
    Purpose:
        Custom option decorator for the node names to receive an action.
    Args:
        action: Deployment action
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @nodes_option("start")
        def foo(nodes: Optional[List[str]]):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--node",
            "nodes",
            multiple=True,
            required=required,
            type=str,
            default=None,  # WARNING: this actually defaults to an empty tuple: https://click.palletsprojects.com/en/8.1.x/options/#multiple-options
            help=f"What individual RACE node(s) to {action} (or all if not specified)",
        )(function)

    return wrapper


def _use_default_race_core():
    value = github_utils.default_race_core_source()
    logger.info(f"Using default RACE core: {value}")
    return value


def _parse_race_core(
    context: click.Context, param: click.Parameter, value: Any
) -> plugin_utils.KitSource:
    source = plugin_utils.parse_kit_source(value)
    return plugin_utils.apply_race_core_defaults(source)


def race_core_option(
    command_help: str = "RACE core to use",
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for RACE core source.
    Args:
        command_help: Help description
        group: Optional parent group
    Return:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @race_core_option()
        def foo(race_core: plugin_utils.KitSource):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--race-core",
            callback=_parse_race_core,
            default=_use_default_race_core,
            help=command_help,
            type=str,
        )(function)

    return wrapper


def race_log_level_option(
    command_help: str = "RACE application log level",
    default: Optional[str] = None,
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator for RACE application log level.
    Args:
        command_help: Help description
        group: Optional parent group
    Return:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @race_log_level_option()
        def foo(race_log_level: Optional[str]):
            pass
    """

    def wrapper(function):
        return group.option(
            "--race-log-level",
            default=default,
            help=command_help,
            type=click.Choice(["debug", "info", "warning", "error"]),
        )(function)

    return wrapper


def _normalize_race_node_arch(
    context: click.Context, param: click.Parameter, value: Any
) -> str:
    """Normalize the RACE node architecture value"""
    if "arm" in value:
        return "arm64-v8a"
    elif "x86" in value:
        return "x86_64"
    return value


def race_node_arch_option(
    choices: Optional[List[str]] = None,
    command_help: str = "Architecture to use for RACE nodes",
    group: click.Group = click,
    normalize: bool = True,
    param: str = "--race-node-arch",
):
    """
    Purpose:
        Custom option decorator for RACE node architecture.
    Args:
        command_help: Help description
        group: Optional parent group
        normalize: Whether to normalize the architecture value
    Return:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @race_node_arch_option()
        def foo(race_node_arch: str):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            param,
            callback=_normalize_race_node_arch if normalize else None,
            envvar="HOST_ARCHITECTURE",
            help=command_help,
            show_choices=False,
            type=click.Choice(
                choices if choices else ["arm", "arm64", "arm64-v8a", "x86", "x86_64"]
            ),
        )(function)

    return wrapper


def range_config_option(
    command_help: str = "Location of range-config file",
    default: str = None,
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the range-config file location.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        required: if option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @range_config_option()
        def foo(range_config: Optional[str]):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--range",
            "range_config",
            default=default,
            help=command_help,
            required=required,
            type=str,
        )(function)

    return wrapper


def disable_config_encryption_option(
    group: click.Group = click,
):
    """
    Purpose:
        Custom option decorator to disable config file encryption for a deployment.
    Args:
        group: Optional parent group
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @disable_config_encryption_option()
        def foo(disable_config_encryption: bool):
            pass
        ```
    """

    command_help = "Disable encryption of config files and all plugin storage files in a deployment"

    def wrapper(function):
        return group.option(
            "--disable-config-encryption",
            flag_value=True,
            help=command_help,
        )(function)

    return wrapper


def network_manager_kit_option(
    command_help: str = "Network manager kit to use",
    default: str = "core=plugin-network-manager-twosix-cpp",
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the network manager kit source.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @network_manager_kit_option()
        def foo(network_manager_kit: plugin_utils.KitSource):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--network-manager-kit",
            callback=_parse_kit_source,
            default=use_default_value("Network manager kit", default),
            help=command_help,
            required=required,
            type=str,
        )(function)

    return wrapper


def network_manager_bypass_route_option(
    flag: Optional[bool] = None,
    command_help: str = "Channel ID, link ID, or connection ID on which to send messages bypassing the network manager plugin (use '*' for any available channel)",
):
    """
    Purpose:
        Custom option decorator for the network-manager-bypass route.
    Args:
        flag: Use option as a switch flag rather than a value option
        command_help: Help description
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @network_manager_bypass_route_option()
        def foo(network_manager_bypass_route: str):
            pass
        ```
    """

    def wrapper(function):
        return click.option(
            "--network-manager-bypass",
            "network_manager_bypass_route",
            default="",
            envvar="NETWORK_MANAGER_BYPASS_ROUTE",
            flag_value=flag,
            help=command_help,
            required=False,
            type=str,
        )(function)

    return wrapper


def comms_channels_option(
    command_help: str = "Comms channels to use",
    default: Iterable[str] = (
        "twoSixDirectCpp",
        "twoSixIndirectCpp",
        "twoSixIndirectBootstrapCpp",
    ),
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the comms channels.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @comms_channels_option()
        def foo(comms_channels: List[str]):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--comms-channel",
            "comms_channels",
            callback=_ensure_unique,
            default=use_default_value("Comms channels", default),
            help=command_help,
            multiple=True,
            required=required,
            type=str,
        )(function)

    return wrapper


def comms_kits_option(
    command_help: str = "Comms kits to use",
    default: Iterable[str] = ("core=plugin-comms-twosix-cpp",),
    group: click.Group = click,
    required: bool = False,
):
    """
    Purpose:
        Custom option decorator for the comms kit sources.
    Args:
        command_help: Help description
        default: Default value
        group: Optional parent group
        required: If option is required
    Returns:
        Function decorator
    Example:
        ```
        @click.command("foo")
        @comms_kits_option()
        def foo(comms_kits: List[plugin_utils.KitSource]):
            pass
        ```
    """

    def wrapper(function):
        return group.option(
            "--comms-kit",
            "comms_kits",
            callback=_parse_kit_sources,
            default=use_default_value("Comms kits", default),
            help=command_help,
            multiple=True,
            required=required,
            type=str,
        )(function)

    return wrapper
