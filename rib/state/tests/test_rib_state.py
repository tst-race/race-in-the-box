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
        Test File for rib_state.py
"""

# Python Library Imports
import os
import pathlib
import pytest
import sys
from mock import patch
from unittest import mock

# Local Library Imports
from rib.state.rib_state import RaceInTheBoxState
from rib.utils import error_utils, rib_utils


###
# Mocks/Data Fixtures
###


# N/A


###
# Tests
###


################################################################################
# __init__
################################################################################


def test___init__(monkeypatch) -> int:
    """
    Purpose:
        Test __init__ works
    Args:
        N/A
    """

    # Patch Load State to Do Nothing
    monkeypatch.setattr(
        RaceInTheBoxState, "load_stored_state", lambda x: None, raising=False
    )

    rib_config = rib_utils.load_race_global_configs("production")

    race_in_the_box_state_obj = RaceInTheBoxState(rib_config)

    assert race_in_the_box_state_obj.user_state_file == (
        f"{rib_config.RIB_PATHS['docker']['user_state']}/"
        f"{rib_config.RIB_USER_STATE_FILENAME}"
    )

    assert "RaceInTheBoxState" in str(race_in_the_box_state_obj)


################################################################################
# verify_rib_state
################################################################################


def test_verify_rib_state_fails_no_file(monkeypatch) -> int:
    """
    Purpose:
        Test verify_rib_state fails
    Args:
        N/A
    """

    # Patch Load State to Do Nothing
    monkeypatch.setattr(
        RaceInTheBoxState, "load_stored_state", lambda x: None, raising=False
    )

    rib_config = rib_utils.load_race_global_configs("production")

    race_in_the_box_state_obj = RaceInTheBoxState(rib_config)
    race_in_the_box_state_obj.user_state_file = ""

    with pytest.raises(error_utils.RIB002):
        with patch("os.path.isfile") as mock_isfile:
            mock_isfile.return_value = False
            race_in_the_box_state_obj.verify_rib_state()


################################################################################
# clear_rib_state
################################################################################


def test_clear_rib_state(monkeypatch) -> int:
    """
    Purpose:
        Test clear_rib_state works
    Args:
        N/A
    """

    # Patch Load State to Do Nothing
    monkeypatch.setattr(
        RaceInTheBoxState, "load_stored_state", lambda x: None, raising=False
    )

    rib_config = rib_utils.load_race_global_configs("production")

    race_in_the_box_state_obj = RaceInTheBoxState(rib_config)

    race_in_the_box_state_obj.rib_mode = "local"
    race_in_the_box_state_obj.verbosity = 2

    race_in_the_box_state_obj.clear_rib_state()

    assert race_in_the_box_state_obj.rib_mode == None
    assert race_in_the_box_state_obj.verbosity == None


################################################################################
# initalize_rib_state
################################################################################


def test_initalize_rib_state(monkeypatch) -> int:
    """
    Purpose:
        Test initalize_rib_state works
    Args:
        N/A
    """

    # Patch Load State to Do Nothing
    monkeypatch.setattr(
        RaceInTheBoxState, "load_stored_state", lambda x: None, raising=False
    )

    rib_config = rib_utils.load_race_global_configs("production")

    race_in_the_box_state_obj = RaceInTheBoxState(rib_config)

    race_in_the_box_state_obj.initalize_rib_state(
        rib_mode="local",
        detail_level=0,
        verbosity=0,
    )

    assert race_in_the_box_state_obj.rib_mode == "local"
    assert race_in_the_box_state_obj.verbosity == 0


################################################################################
# set_rib_mode
################################################################################


def test_set_rib_mode() -> int:
    """
    Purpose:
        Test set_rib_mode works
    Args:
        N/A
    """

    with mock.patch("builtins.input", return_value="local"):
        RaceInTheBoxState.set_rib_mode(RaceInTheBoxState, "local")
        assert RaceInTheBoxState.rib_mode == "local"


################################################################################
# set_detail_level
################################################################################


def test_set_detail_level() -> int:
    """
    Purpose:
        Test set_detail_level works
    Args:
        N/A
    """

    RaceInTheBoxState.set_detail_level(RaceInTheBoxState, 1)
    assert RaceInTheBoxState.detail_level == 1

    with mock.patch("sys.stdin.isatty", return_value=True):
        with mock.patch("click.prompt", return_value=2):
            RaceInTheBoxState.set_detail_level(RaceInTheBoxState, None)
            assert RaceInTheBoxState.detail_level == 2

    with mock.patch("sys.stdin.isatty", return_value=False):
        RaceInTheBoxState.detail_level = 0
        RaceInTheBoxState.set_detail_level(RaceInTheBoxState, None)
        assert RaceInTheBoxState.detail_level == 0


################################################################################
# set_verbosity
################################################################################


def test_set_verbosity() -> int:
    """
    Purpose:
        Test set_verbosity works
    Args:
        N/A
    """

    RaceInTheBoxState.set_verbosity(RaceInTheBoxState, 1)
    assert RaceInTheBoxState.verbosity == 1

    with mock.patch("sys.stdin.isatty", return_value=True):
        with mock.patch("click.prompt", return_value=2):
            RaceInTheBoxState.set_verbosity(RaceInTheBoxState, None)
            assert RaceInTheBoxState.verbosity == 2

    with mock.patch("sys.stdin.isatty", return_value=False):
        RaceInTheBoxState.verbosity = 0
        RaceInTheBoxState.set_verbosity(RaceInTheBoxState, None)
        assert RaceInTheBoxState.verbosity == 0


################################################################################
# export_state
################################################################################


def test_export_state(monkeypatch) -> int:
    """
    Purpose:
        Test export_state works
    Args:
        N/A
    """

    # Patch Load State to Do Nothing
    monkeypatch.setattr(
        RaceInTheBoxState, "load_stored_state", lambda x: None, raising=False
    )

    rib_config = rib_utils.load_race_global_configs("production")
    race_in_the_box_state_obj = RaceInTheBoxState(rib_config)

    race_in_the_box_state_obj.initalize_rib_state(
        rib_mode="local",
        detail_level=0,
        verbosity=0,
    )
    returned_state = race_in_the_box_state_obj.export_state()

    assert returned_state == {
        "rib_mode": "local",
        "detail_level": 0,
        "verbosity": 0,
    }


################################################################################
# load_stored_state
################################################################################


def test_load_stored_state(monkeypatch, tmp_path: pathlib.PosixPath) -> int:
    """
    Purpose:
        Test load_stored_state works
    Args:
        N/A
    """

    rib_config = rib_utils.load_race_global_configs("production")
    race_in_the_box_state_obj = RaceInTheBoxState(rib_config)

    race_in_the_box_state_obj.initalize_rib_state(
        rib_mode="local",
        detail_level=0,
        verbosity=0,
    )

    # Temp dir for storing state
    state_file = tmp_path / "test"

    # Store state
    race_in_the_box_state_obj.user_state_file = state_file
    race_in_the_box_state_obj.store_state()

    # Create new obj and load state
    race_in_the_box_state_obj2 = RaceInTheBoxState(rib_config)
    race_in_the_box_state_obj2.user_state_file = state_file
    race_in_the_box_state_obj2.load_stored_state()

    returned_state = race_in_the_box_state_obj2.export_state()

    assert returned_state == {
        "rib_mode": "local",
        "detail_level": 0,
        "verbosity": 0,
    }


################################################################################
# store_state
################################################################################


def test_store_state(monkeypatch, tmp_path: pathlib.PosixPath) -> int:
    """
    Purpose:
        Test store_state works
    Args:
        N/A
    """

    # Patch Load State to Do Nothing
    monkeypatch.setattr(
        RaceInTheBoxState, "load_stored_state", lambda x: None, raising=False
    )

    rib_config = rib_utils.load_race_global_configs("production")
    race_in_the_box_state_obj = RaceInTheBoxState(rib_config)

    race_in_the_box_state_obj.initalize_rib_state(
        rib_mode="local",
        detail_level=0,
        verbosity=0,
    )

    race_in_the_box_state_obj.user_state_file = tmp_path / "test"
    race_in_the_box_state_obj.store_state()

    assert os.path.isfile(race_in_the_box_state_obj.user_state_file)
