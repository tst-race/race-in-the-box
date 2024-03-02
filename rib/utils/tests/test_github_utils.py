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
    Tests for github_utils.py
"""

# Python Library Imports
import pytest
from mock import patch

# Local Library Imports
from rib.utils import github_utils


@pytest.mark.parametrize(
    "image,expected",
    [
        (
            "domain.name/gh-org/gh-repo/image:tag",
            "domain.name/gh-org/gh-repo/image:tag",
        ),
        (
            "domain.name:port/gh-org/gh-repo/image",
            "domain.name:port/gh-org/gh-repo/image",
        ),
        ("gh-org/gh-repo/image", "gh-org/gh-repo/image"),
        ("gh-repo/image:tag", "gh-repo/image:tag"),
        ("image:tag", "image:tag"),
        ("image", "image"),
        (":tag", "ghcr.io/def-org/def-repo/def-image:tag"),
    ],
)
@patch("rib.utils.github_utils._config")
def test_apply_defaults_to_image(mock_config, image, expected):
    mock_config.return_value = github_utils.GitHubConfig(
        default_race_images_org="def-org",
        default_race_images_repo="def-repo",
        default_race_images_tag="def-tag",
    )
    if isinstance(expected, str):
        assert expected == github_utils.apply_defaults_to_image(image, "def-image")
    else:
        with pytest.raises(expected):
            github_utils.apply_defaults_to_image(image, "def-image")


@pytest.mark.parametrize(
    "default_org,default_repo,default_tag,expected",
    [
        ("def-org", "def-repo", None, "ghcr.io/def-org/def-repo/def-image:tag"),
        ("def-org", None, None, "ghcr.io/def-org/race-images/def-image:tag"),
        (None, None, None, "ghcr.io/fallback/race-images/def-image:tag"),
    ],
)
@patch("rib.utils.github_utils._config")
def test_apply_defaults_to_image_defaults(
    mock_config, default_org, default_repo, default_tag, expected
):
    mock_config.return_value = github_utils.GitHubConfig(
        default_org="fallback",
        default_race_images_org=default_org,
        default_race_images_repo=default_repo,
        default_race_images_tag=default_tag,
    )
    assert expected == github_utils.apply_defaults_to_image(":tag", "def-image")
