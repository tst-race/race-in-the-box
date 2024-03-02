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
        Test File for elasticsearch_utils.py
"""

# Python Library Imports
import os
import sys
import pytest
from unittest import mock

# Local Library Imports
from rib.utils import elasticsearch_utils, error_utils, config_utils


###
# Fixtures
###


# None at the Moment (Empty Test Suite)


###
# Mocked Functions
###


# None at the Moment (Empty Test Suite)


###
# Test config_utils functions
###


# None at the Moment (Empty Test Suite)

################################################################################
# check_valid_config_options
################################################################################


def test_get_message_spans():
    """
    Purpose:
        Test get_message_spans parses elasticsearch query result
    """
    sample_input = [
        {
            "_index": "jaeger-span-2022-01-27",
            "_type": "_doc",
            "_id": "SEVenH4Bo4OrMeytWHJn",
            "_score": None,
            "_source": {
                "traceID": "f55d3ec8682fd7fd",
                "spanID": "f55d3ec8682fd7fd",
                "flags": 1,
                "operationName": "sendMessage",
                "references": [],
                "startTime": 1643300930225336,
                "startTimeMillis": 1643300930225,
                "duration": 10136,
                "tags": [
                    {"key": "sampler.type", "type": "string", "value": "const"},
                    {"key": "sampler.param", "type": "bool", "value": "true"},
                    {"key": "source", "type": "string", "value": "racetestapp"},
                    {
                        "key": "file",
                        "type": "string",
                        "value": "/builds/race-common/racesdk/racetestapp-shared/source/RaceTestApp.cpp",
                    },
                    {"key": "messageSize", "type": "string", "value": "13"},
                    {
                        "key": "messageHash",
                        "type": "string",
                        "value": "d746f5d9f211a51e02206aea9a78bee9110f0a9d",
                    },
                    {
                        "key": "messageFrom",
                        "type": "string",
                        "value": "race-client-00001",
                    },
                    {
                        "key": "messageTo",
                        "type": "string",
                        "value": "race-client-00002",
                    },
                    {"key": "messageTestId", "type": "string", "value": "default"},
                    {"key": "internal.span.format", "type": "string", "value": "proto"},
                ],
                "logs": [],
                "process": {
                    "serviceName": "race-client-00001",
                    "tags": [
                        {
                            "key": "jaeger.version",
                            "type": "string",
                            "value": "C++-0.6.0",
                        },
                        {
                            "key": "hostname",
                            "type": "string",
                            "value": "race-client-00001",
                        },
                        {"key": "ip", "type": "string", "value": "10.11.0.13"},
                    ],
                },
            },
            "fields": {"startTimeMillis": ["1643300930225"]},
            "sort": [1643300930225],
        }
    ]

    expected_span = elasticsearch_utils.MessageSpan(
        trace_id="f55d3ec8682fd7fd",
        span_id="f55d3ec8682fd7fd",
        start_time=1643300930225336,
        source_persona="race-client-00001",
        messageSize="13",
        messageHash="d746f5d9f211a51e02206aea9a78bee9110f0a9d",
        messageTestId="default",
        messageFrom="race-client-00001",
        messageTo="race-client-00002",
    )

    expected_output = (
        {expected_span["source_persona"]: [expected_span]},
        {expected_span["trace_id"]: [expected_span]},
    )

    result = elasticsearch_utils.get_message_spans(sample_input)

    assert result == expected_output
