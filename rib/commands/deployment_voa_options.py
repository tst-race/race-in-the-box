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
    Custom decorators to standardize click options for VoA commands
"""

# Python Library Imports
import click
from typing import Any, Callable, Dict

from rib.commands.option_group import MutuallyExclusiveOptions
from rib.utils.voa_utils import VoaRule


def voa_duration_options(func: Callable) -> Callable:
    """
    Purpose:
        Define common voa duration options for the given command function
    Args:
        func: Click command function
    Returns:
        Decorated function
    """

    ###
    # Mutually exclusive options for duration strategy
    ###

    durationstrategy = MutuallyExclusiveOptions()
    duration_holdtime_strategy = durationstrategy.group(
        "duration-holdtime-strategy", name="Duration strategy - holdtime (default)"
    )
    duration_jitter_strategy = durationstrategy.group(
        "duration-jitter-strategy", name="Duration strategy - jitter"
    )

    func = duration_holdtime_strategy.option(
        "--hold-time",
        "hold_time",
        required=False,
        default="0",
        show_default=True,
        help="The duration (in seconds) that the package should be held prior to being sent.",
    )(func)
    func = duration_jitter_strategy.option(
        "--jitter",
        "jitter",
        required=False,
        default="0",
        show_default=True,
        help="Maximum bounds (in seconds) for a random jitter that needs to be introduced",
    )(func)

    func = durationstrategy.result(
        "durationstrategy",
        default=duration_holdtime_strategy.key,
    )(func)
    return func


def voa_rule_options(func: Callable) -> Callable:
    """
    Purpose:
        Define voa rule options for the given command function
    Args:
        func: Click command function
    Returns:
        Decorated function
    """

    ###
    # Mutually exclusive options for window strategy
    ###

    windowstrategy = MutuallyExclusiveOptions()
    window_duration_strategy = windowstrategy.group(
        "window-duration-strategy", name="Window strategy - duration"
    )
    window_count_strategy = windowstrategy.group(
        "window-count-strategy", name="Window strategy - count"
    )
    func = window_duration_strategy.option(
        "--window-duration",
        "window_duration",
        help="Time duration for application of the rule",
        required=False,
        type=str,
        default="",
    )(func)
    func = window_count_strategy.option(
        "--window-count",
        "window_count",
        help="The number of packages that should be processed through the rule",
        required=False,
        type=str,
        default="",
    )(func)

    ###
    # Mutually exclusive options for trigger strategy
    ###

    triggerstrategy = MutuallyExclusiveOptions()
    trigger_prob_strategy = triggerstrategy.group(
        "trigger-prob-strategy", name="Trigger strategy - probability"
    )
    trigger_skip_strategy = triggerstrategy.group(
        "trigger-skip-strategy", name="Trigger strategy - skip"
    )
    func = trigger_prob_strategy.option(
        "--trigger-probability",
        "trigger_probability",
        help="Trigger probability",
        required=False,
        type=str,
        default="",
    )(func)
    func = trigger_skip_strategy.option(
        "--trigger-skip",
        "trigger_skip",
        help="Trigger skip times",
        required=False,
        type=str,
        default="",
    )(func)

    ###
    # Common command options
    ###

    func = click.option(
        "--rule-id",
        "rule_id",
        help="Rule identifier",
        required=True,
        type=str,
    )(func)
    func = click.option(
        "--dir",
        "rule_direction",
        help="Rule direction (currently only 'to' supported)",
        required=False,
        type=click.Choice(["to"]),
        default="to",
        show_default=True,
    )(func)
    func = click.option(
        "--match-type",
        "match_type",
        help="Target match type",
        required=False,
        type=click.Choice(["persona", "link", "channel"]),
        default="persona",
        show_default=True,
    )(func)
    func = click.option(
        "--match-value",
        "match_value",
        help="Target match value",
        required=False,
        type=str,
        default="all",
        show_default=True,
    )(func)
    func = click.option(
        "--tag",
        "tag",
        help="Tag string",
        required=False,
        type=str,
        default="",
    )(func)
    func = click.option(
        "--startup-delay",
        "startup_delay",
        help="Startup delay",
        required=False,
        type=str,
        default="",
    )(func)

    ###
    # Chain with mutually exclusive options
    ###

    func = windowstrategy.result("windowstrategy", expose_value=False)(func)
    func = triggerstrategy.result("triggerstrategy", expose_value=False)(func)

    return func


def voa_delete_options(func: Callable) -> Callable:
    """
    Purpose:
        Define delete options
    Args:
        func: Click command function
    Returns:
        Decorated function
    """

    ###
    # Mutually exclusive options for rule-id and all
    ###

    delete_target = MutuallyExclusiveOptions()
    rule_strategy = delete_target.group("ruleid-strategy", name="Single rule deletion")
    all_strategy = delete_target.group("all-strategy", name="Delete all rules")

    func = rule_strategy.option(
        "--rule-id",
        "rule_id_list",
        help="Rule identifier",
        required=False,
        multiple=True,
        type=str,
        default=None,
    )(func)
    func = all_strategy.option(
        "--all",
        "all_rules",
        help="Delete all rules",
        required=False,
        is_flag=True,
        default=False,
    )(func)

    func = delete_target.result("deletetarget", expose_value=False)(func)
    return func
