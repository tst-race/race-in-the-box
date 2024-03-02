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
        Utilities for VoA operations
"""

# Python Library Imports
from typing import Dict, TypedDict, Optional

# Local Python Library Imports
# N/A

###
# Types
###


class VoaRule(TypedDict):
    """VoA Rule Information"""

    rule_id: str
    "The rule identifier"

    rule_direction: str
    "The direction of the rule (to or from)"

    match_type: str
    "the type of identifier to match (persona, linkId, channel)"

    match_value: str
    "the value of the identifier"

    tag: str
    "A tag string"

    startup_delay: str
    "The number of seconds to wait prior to the rule going into effect"

    trigger_probability: str
    "The probability of triggering this rule"

    trigger_skip: str
    "The number of packages to skip between each application of the rule"

    window_duration: str
    "The time duration for application of the rule"

    window_count: str
    "The number of packages that should be processed through the rule"

    durationstrategy: Optional[str]
    "strategy: whether jitter or holdtime"

    jitter: Optional[str]
    "maximum jitter (valid for delay and replay)"

    hold_time: Optional[str]
    "the hold time (valid for delay and replay)"

    replay_times: Optional[str]
    "number of times to replay a package (valid for replay)"

    iterations: Optional[str]
    "number of times to apply the tamper operation"


###
# Rule construction functions
###


def construct_voa_rule(
    node: str,
    rule_action: str,
    **rule: VoaRule,
) -> Dict:
    """
    Purpose:
        return a rule payload for the given set of params
    Args:
        node: Persona of the RACE node on which rule is to be applied
        rule_action: The specific VoA action to perform (delay, drop, tamper, replay)
        rule: Rule parameters
    Return:
        voa_config (Dict): VoA configuration dictionary
    """

    # Fill in required pieces of rule
    rule_payload = {
        "persona": node,
        "action": rule_action,
        "params": {},
        "trigger": {},
        "window": {},
        "tag": rule["tag"],
        "startupdelay": rule["startup_delay"],
        rule["rule_direction"]: {
            "type": rule["match_type"],
            "matchid": rule["match_value"],
        },
    }

    # Add action parameters if specified
    if "durationstrategy" in rule:
        if rule["durationstrategy"] == "duration-holdtime-strategy":
            rule_payload["params"]["holdtime"] = rule["hold_time"]
        elif rule["durationstrategy"] == "duration-jitter-strategy":
            rule_payload["params"]["jitter"] = rule["jitter"]
    if "replay_times" in rule:
        rule_payload["params"]["replaytimes"] = rule["replay_times"]
    if "iterations" in rule:
        rule_payload["params"]["iterations"] = rule["iterations"]

    # Add other payload sections only if parameters exist
    if rule["trigger_probability"]:
        rule_payload["trigger"]["prob"] = rule["trigger_probability"]
    if rule["trigger_skip"]:
        rule_payload["trigger"]["skipN"] = rule["trigger_skip"]
    if rule["window_duration"]:
        rule_payload["window"]["duration"] = rule["window_duration"]
    if rule["window_count"]:
        rule_payload["window"]["count"] = rule["window_count"]

    voa_config = {rule["rule_id"]: rule_payload}

    return voa_config
