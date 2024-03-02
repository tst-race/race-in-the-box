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
    Utilities for logging
"""

# Python Library Imports
import click
import click_log
import logging
import os
from datetime import date
from typing import List


TRACE = 5
root_logger = logging.getLogger()


def _logger_trace(self, message, *args, **kwargs) -> None:
    """
    Purpose:
        Logs a trace-level message to the current logger
    Args:
        self: Current logger
        message: Log message
        args: Positional arguments
        kwargs: Keyword arguments
    Returns:
        N/A
    """
    if self.isEnabledFor(TRACE):
        # yes, _log takes in args not *args
        self._log(TRACE, message, args, **kwargs)  # pylint: disable=protected-access


def _module_trace(message, *args, **kwargs) -> None:
    """
    Purpose:
        Logs a trace-level message to the root logger
    Args:
        message: Log message
        args: Positional arguments
        kwargs: Keyword arguments
    Returns:
        N/A
    """
    root_logger.trace(message, *args, **kwargs)


def setup_logger(config: "rib.config.Config", log_to_stdout: bool = True) -> None:
    """
    Purpose:
        Set up logging for RiB.

        If the CI environment variable is set to true or 1, then colorized log
        output is disabled.

        This will also define a trace log level. This can be used throughout the
        RiB code
    Args:
        config: RiB configuration
        log_to_stdout: Whether to log output to stdout in addition to the log file
    Returns:
        N/A
    """
    if log_to_stdout:
        click_log.basic_config()

    # We want logs to go to stdout, not stderr
    click_log.ClickHandler._use_stderr = False  # pylint: disable=protected-access

    # If in CI mode, disable all color output
    if os.environ.get("CI", "").lower() in ["true", "yes", "1"]:
        click_log.ColorFormatter.colors = {}
    else:
        click_log.ColorFormatter.colors["trace"] = dict(fg="magenta")

    # Use the RiB container start time so all sessions/shells write to the same filename prefix
    rib_start_time = os.environ.get("RIB_START_TIME")
    if not rib_start_time:
        rib_start_time = date.today().strftime("%Y-%m-%d")

    # Use the parent PID so we use the PID of the shell process rather than
    # the temporary Python interpreter process
    pid = os.getppid()
    if not pid:
        # Parent PID is 0 if it was a rib command as part of a "docker exec"
        pid = os.getpid()

    filename = f"{config.RIB_PATHS['docker']['rib_logs']}/{rib_start_time}-{pid}.log"
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)-8s %(name)s : %(message)s")
    )
    root_logger.addHandler(file_handler)

    # Set up "command" logger to *only* get written to the file, not the console
    # (this is used to log the executed RiB command & duration to just the file)
    command_logger = logging.getLogger("command")
    # Enable debug level on this logger so that command duration is recorded
    command_logger.setLevel(logging.DEBUG)
    command_logger.propagate = False
    command_logger.addHandler(file_handler)

    register_trace_log_level()
    _set_level(None, None, 0)


def register_trace_log_level() -> None:
    """
    Purpose:
        Register custom trace log level
    Args:
        N/A
    Returns:
        N/A
    """
    logging.TRACE = TRACE
    logging.addLevelName(TRACE, "TRACE")
    logging.Logger.trace = _logger_trace
    logging.trace = _module_trace


def _set_level(_ctx: click.Context, _param: str, verbosity: int) -> None:
    """
    Purpose:
        Set the root logger level based on the given verbosity

        Verbosity levels:
            0 = INFO only
            1 = DEBUG enabled for "rib" loggers
            2 = TRACE enabled for "rib" loggers
            3 = TRACE enabled for all loggers (3rd party libs)
    Args:
        _ctx: Click context (not used)
        _param: Option parameter name (not used)
        verbosity: the verbosity level
    Returns:
        N/A
    """
    if verbosity is None:
        return

    # Baseline is to log everything under rib, but only INFO for everything else
    # (i.e., suppress debug logs from 3rd party libs)
    root_logger.setLevel(logging.INFO)
    logging.getLogger("rib").setLevel(logging.TRACE)

    if verbosity > 2:
        # Open up all logging to debug/trace level (console and file get everything)
        root_logger.setLevel(logging.TRACE)
        logging.getLogger("paramiko").setLevel(logging.DEBUG)
    else:
        # Suppress info-level logs from paramiko
        logging.getLogger("paramiko").setLevel(logging.WARNING)

    level = logging.INFO
    if verbosity > 1:
        level = logging.TRACE
    elif verbosity > 0:
        level = logging.DEBUG
    # Only set the level for the click-log handler (file handler gets everything)
    root_logger.handlers[0].setLevel(level)


def _create_verbose_option(ctx: click.Context) -> click.Option:
    """
    Purpose:
        Creates a verbosity option to set logging level through counted
        option parameter, using a default value from the context/RiB state
    Args:
        ctx: Click context
    Returns:
        Click option
    """
    return click.Option(
        ["-v"],
        callback=_set_level,
        count=True,
        default=ctx.obj and ctx.obj.verbosity or 0,
        expose_value=False,
        help="Increase logging verbosity",
        show_default=True,
    )


def _create_quiet_option() -> click.Option:
    """
    Purpose:
        Creates a hidden quiet option to reset the logging verbosity level
        to 0/info. This is useful since you can't reset a counted option back
        to 0 when it has a default non-zero value.

        It re-uses the _set_level callback with a hard-coded verbosity value of 0.
    Args:
        N/A
    Returns:
        Click option
    """
    return click.Option(
        ["--quiet", "-q"],
        callback=_set_level,
        expose_value=False,
        flag_value=0,
        type=int,
        hidden=True,
        help="Suppress verbose logging",
    )


def setup_global_verbosity_option() -> None:
    """
    Purpose:
        Adds a global verbosity option to all click commands. This option is not
        exposed to commands, but instead sets the root logger level.

        Defining a global/automatic option is achieved by monkey-patching/extending
        the click.Command.get_params method to add the verbose/quiet options. This
        method is where the global help option is automatically added to all
        commands, so we're doing the same for our custom global options.
    Args:
        N/A
    Returns:
        N/A
    """

    orig_get_params = click.Command.get_params

    def _get_params(self, ctx: click.Context) -> List[click.Parameter]:
        """
        Purpose:
            Add verbose & quiet options to command parameters
        Args:
            self: The Command instance
            ctx: Click context
        Returns:
            List of command parameters
        """
        params = orig_get_params(self, ctx)
        # insert 2nd to last so help is still the last parameter
        params.insert(-1, _create_verbose_option(ctx))
        params.insert(-1, _create_quiet_option())
        return params

    click.Command.get_params = _get_params
