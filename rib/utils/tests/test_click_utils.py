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
        Test File for click_utils.py
"""

# Python Library Imports
import click
import os
import sys
import pytest
from dataclasses import dataclass, field
from mock import patch
from typing import Any, Dict, List, Type
from unittest import mock
from unittest.mock import MagicMock

# Local Library Imports
from rib.utils import click_utils


###
# Fixtures/Mocks
###


@pytest.fixture
def mock_command_function() -> None:
    """A mock command function"""
    pass


class MockContextObj:
    """A mock command"""

    pass


@dataclass
class MockCommandParam:
    """A Mock command Param"""

    name: str
    opts: str
    count: int = 0


@dataclass
class MockCommandCommand:
    """A Mock command Param"""

    params: List[MockCommandParam]


@dataclass
class MockCommand:
    """A Mock command Param"""

    command_path: str
    info_name: str
    command: MockCommandCommand
    args: List[str]
    params: Dict[str, Any]
    parent: Type["MockCommand"]


###
# Test Functionality
###


######
# get_click_arguments
######


def test_get_click_arguments() -> int:
    """
    Purpose:
        Test get_click_arguments properly returns expected args
    Args:
        N/A
    """

    assert click_utils.get_click_arguments() == []
    assert (
        click_utils.get_click_arguments(
            command_args=None,
            command_kwargs=None,
            command_flags=None,
        )
        == []
    )
    assert (
        click_utils.get_click_arguments(
            command_args=[],
            command_kwargs={},
            command_flags=[],
        )
        == []
    )
    assert click_utils.get_click_arguments(
        command_args=["--x"],
        command_kwargs={"--y": 1},
        command_flags=["--z"],
    ) == ["--x", "--y", 1, "--z"]


def test_call_click_command(
    mock_command_function,
) -> int:
    """
    Purpose:
        Test call_click_command properly returns expected args
    Args:
        N/A
    """

    with mock.patch("click.testing.CliRunner") as mock_click_testing:
        mock_command_result = click_utils.call_click_command(
            mock_command_function, MockContextObj(), []
        )
        assert mock_command_result._extract_mock_name() == "CliRunner().invoke()"
        assert mock_click_testing.called


def test_get_run_command() -> int:
    """
    Purpose:
        Test get_run_command properly returns expected args
    Args:
        N/A
    """

    mock_command_command = MockCommandCommand(
        params=[
            MockCommandParam(
                name="empty_param",
                opts=["--empty-param"],
            ),
            MockCommandParam(
                name="str_param",
                opts=["--str-param"],
            ),
            MockCommandParam(
                name="int_param",
                opts=["--int-param"],
            ),
            MockCommandParam(
                name="list_param",
                opts=["--list-param"],
            ),
            MockCommandParam(
                name="bool_param",
                opts=["--bool-param"],
            ),
            MockCommandParam(
                count=True,
                name="count_param",
                opts=["--count-param"],
            ),
        ]
    )

    mock_command_1 = MockCommand(
        command_path="test1",
        info_name="test1",
        command=mock_command_command,
        args=["--arg1", "--arg2"],
        params={
            "empty_param": None,
            "str_param": "test",
            "int_param": 1,
            "bool_param": True,
            "list_param": ["1", "2"],
            "count_param": 2,
        },
        parent=None,
    )
    mock_command_2 = MockCommand(
        command_path="test1 test2",
        info_name="test2",
        command=mock_command_command,
        args=["--arg1", "--arg2"],
        params={
            "empty_param": None,
            "str_param": "test",
            "int_param": 1,
            "bool_param": False,
            "list_param": ["1", "2"],
            "count_param": 2,
        },
        parent=mock_command_1,
    )

    assert (
        click_utils.get_run_command(mock_command_2)
        == "test1 --arg1 --arg2 --str-param=test --int-param=1 --bool-param --list-param=1 --list-param=2 --count-param --count-param test2 --arg1 --arg2 --str-param=test --int-param=1 --list-param=1 --list-param=2 --count-param --count-param"
    )
