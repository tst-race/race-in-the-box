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
    Tests for plugin_utils.py
"""

# Python Library Imports
from typing import List
import pytest
from unittest.mock import MagicMock
from mock import patch

# Local Library Imports
from rib.utils import plugin_utils, error_utils


# Test Static Functions


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("", error_utils.RIB500),
        ("file=/plugin/path", error_utils.RIB500),
        ("corePlugin,corePlugin", error_utils.RIB500),
        ("corePlugin", error_utils.RIB500),
        (
            "core=corePlugin",
            plugin_utils.KitSource(
                raw="core=corePlugin", source_type="core", asset="corePlugin.tar.gz"
            ),
        ),
        ("core=corePlugin,core=corePlugin", error_utils.RIB500),
        (
            "local=/plugin/path",
            plugin_utils.KitSource(
                raw="local=/plugin/path", source_type="local", uri="/plugin/path"
            ),
        ),
        ("core=corePlugin,local=/plugin/path", error_utils.RIB500),
        (
            "remote=https://race.com/plugin.tar.gz",
            plugin_utils.KitSource(
                raw="remote=https://race.com/plugin.tar.gz",
                source_type="remote",
                uri="https://race.com/plugin.tar.gz",
            ),
        ),
        ("core=corePlugin,remote=https://race.com/plugin.tar.gz", error_utils.RIB500),
        (
            "tag=1.0.0",
            plugin_utils.KitSource(
                raw="tag=1.0.0",
                source_type="gh_tag",
                tag="1.0.0",
            ),
        ),
        (
            "tag=1.0.0,repo=plugin-repo",
            plugin_utils.KitSource(
                raw="tag=1.0.0,repo=plugin-repo",
                source_type="gh_tag",
                tag="1.0.0",
                repo="plugin-repo",
            ),
        ),
        ("tag=https://github.com/gh-org/plugin-repo/1.0.0", error_utils.RIB500),
        (
            "tag=https://github.com/gh-org/plugin-repo/releases/tag/1.0.0",
            plugin_utils.KitSource(
                raw="tag=https://github.com/gh-org/plugin-repo/releases/tag/1.0.0",
                source_type="gh_tag",
                org="gh-org",
                repo="plugin-repo",
                tag="1.0.0",
            ),
        ),
        (
            "tag=https://github.com/gh-org/plugin-repo/releases/download/1.0.0/tag-asset.zip",
            plugin_utils.KitSource(
                raw="tag=https://github.com/gh-org/plugin-repo/releases/download/1.0.0/tag-asset.zip",
                source_type="gh_tag",
                org="gh-org",
                repo="plugin-repo",
                tag="1.0.0",
                asset="tag-asset.zip",
            ),
        ),
        ("core=corePlugin,tag=1.0.0", error_utils.RIB500),
        (
            "branch=develop",
            plugin_utils.KitSource(
                raw="branch=develop",
                source_type="gh_branch",
                branch="develop",
            ),
        ),
        (
            "branch=develop,org=gh-org",
            plugin_utils.KitSource(
                raw="branch=develop,org=gh-org",
                source_type="gh_branch",
                branch="develop",
                org="gh-org",
            ),
        ),
        ("core=corePlugin,branch=develop", error_utils.RIB500),
        (
            "run=12341234",
            plugin_utils.KitSource(
                raw="run=12341234",
                source_type="gh_action_run",
                run="12341234",
            ),
        ),
        (
            "org=gh-org,repo=plugin-repo,run=12341234",
            plugin_utils.KitSource(
                raw="org=gh-org,repo=plugin-repo,run=12341234",
                source_type="gh_action_run",
                run="12341234",
                org="gh-org",
                repo="plugin-repo",
            ),
        ),
        ("core=corePlugin,run=12341234", error_utils.RIB500),
    ],
)
def test_parse_kit_source(raw, expected):
    if isinstance(expected, plugin_utils.KitSource):
        assert expected == plugin_utils.parse_kit_source(raw)
    else:
        with pytest.raises(expected):
            plugin_utils.parse_kit_source(raw)


###
# channel_plugin_has_external_services
###


@patch("os.path.exists", MagicMock(return_value=True))
def test_channel_plugin_has_external_services_scripts_exist():
    """
    Purpose:
        Test channel_plugin_has_external_services will return True when all scripts
        are present
    Args
        N/A
    """
    assert plugin_utils.channel_plugin_has_external_services(
        "test_channel", "test_path"
    )


@patch("os.path.exists", MagicMock(return_value=False))
def test_channel_plugin_has_external_services_missing_all_scripts():
    """
    Purpose:
        Test channel_plugin_has_external_services will return True when all scripts
        are missing
    Args
        N/A
    """
    assert not plugin_utils.channel_plugin_has_external_services(
        "test_channel", "test_path"
    )


def test_channel_plugin_has_external_services_missing_some_scripts():
    """
    Purpose:
        Test channel_plugin_has_external_services will return True when some scripts
        are missing. Should also log and error
    Args
        N/A
    """

    with patch("os.path.exists") as os_path_mock:
        os_path_mock.side_effect = [True, True, False]
        assert not plugin_utils.channel_plugin_has_external_services(
            "test_channel", "test_path"
        )
