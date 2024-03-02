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
        Test File for cli.py
"""

# Python Library Imports
import os
import sys
import pytest
from unittest import mock

# Local Library Imports
from rib.config import config
from rib.config.config import Config


###
# Mocks/Data Fixtures
###


# N/A


###
# Tests
###


################################################################################
# get
################################################################################


def test_get_default(monkeypatch) -> int:
    """
    Purpose:
        Test Config.get defaults to development
    Args:
        N/A
    """

    monkeypatch.setenv("ENVIRONMENT", None, prepend=False)
    retrieved_config = Config.get()
    assert isinstance(retrieved_config, Config.Development)


def test_get_prod() -> int:
    """
    Purpose:
        Test Config.get can get Production
    Args:
        N/A
    """

    retrieved_config = Config.get(environment="prod")
    assert isinstance(retrieved_config, Config.Production)

    retrieved_config = Config.get(environment="production")
    assert isinstance(retrieved_config, Config.Production)


def test_get_qa() -> int:
    """
    Purpose:
        Test Config.get can get QA
    Args:
        N/A
    """

    retrieved_config = Config.get(environment="test")
    assert isinstance(retrieved_config, Config.Qa)

    retrieved_config = Config.get(environment="testing")
    assert isinstance(retrieved_config, Config.Qa)

    retrieved_config = Config.get(environment="qa")
    assert isinstance(retrieved_config, Config.Qa)


def test_get_dev() -> int:
    """
    Purpose:
        Test Config.get can get development
    Args:
        N/A
    """

    retrieved_config = Config.get(environment="dev")
    assert isinstance(retrieved_config, Config.Development)

    retrieved_config = Config.get(environment="development")
    assert isinstance(retrieved_config, Config.Development)


def test_get_unexpected() -> int:
    """
    Purpose:
        Test Config.get provides develop with unexpected values
    Args:
        N/A
    """

    retrieved_config = Config.get(environment="bro")
    assert isinstance(retrieved_config, Config.Development)

    retrieved_config = Config.get(environment="not_a_value")
    assert isinstance(retrieved_config, Config.Development)


def test_get_env_setting(monkeypatch) -> int:
    """
    Purpose:
        Test Config.get provides develop with unexpected values
    Args:
        N/A
    """

    monkeypatch.setenv("ENVIRONMENT", "prod", prepend=False)
    retrieved_config = Config.get()
    assert isinstance(retrieved_config, Config.Production)


################################################################################
# Production
################################################################################


def test_prod() -> int:
    """
    Purpose:
        Test Prod Config
    Args:
        N/A
    """

    retrieved_config = Config.get(environment="prod")
    assert isinstance(retrieved_config, Config.Production)


################################################################################
# QA
################################################################################


def test_qa() -> int:
    """
    Purpose:
        Test QA Config
    Args:
        N/A
    """

    retrieved_config = Config.get(environment="test")
    assert isinstance(retrieved_config, Config.Qa)


################################################################################
# Dev
################################################################################


def test_dev() -> int:
    """
    Purpose:
        Test Dev Config
    Args:
        N/A
    """

    retrieved_config = Config.get(environment="dev")
    assert isinstance(retrieved_config, Config.Development)
