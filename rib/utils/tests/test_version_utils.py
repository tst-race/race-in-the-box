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
    Tests for version_utils.py
"""

# Python Library Imports
import pytest
from typing import Optional

# Local Python Library Imports
from rib.utils import version_utils
from rib.utils.version_utils import Version


###
# version_from_str
###


@pytest.mark.parametrize(
    "version_str,expected",
    [
        ("1.2.3", Version(1, 2, 3, None, False)),
        ("rc-1.2.3", Version(1, 2, 3, None, True)),
        ("1.2.3-hotfix", Version(1, 2, 3, "hotfix", False)),
        ("rc-1.2.3-hotfix", Version(1, 2, 3, "hotfix", True)),
        ("1.2.*", Version(1, 2, None, None, False)),
        ("1.2.*-hotfix", Version(1, 2, None, "hotfix", False)),
        ("latest", None),
        ("1", None),
        ("1.2", None),
        ("1.2.hotfix", None),
        ("a.b.c", None),
    ],
)
def test_version_from_str(version_str: str, expected: Optional[version_utils.Version]):
    if not expected:
        with pytest.raises(version_utils.VersionParseError):
            version_utils.version_from_str(version_str)
    else:
        assert expected == version_utils.version_from_str(version_str)


###
# is_compatible
###


@pytest.mark.parametrize(
    "constraint,version,expected",
    [
        ("1.2.3", "1.2.3", True),
        ("1.2.3", "1.2.2", True),
        ("1.2.3", "1.2.3-hotfix", True),
        ("1.2.3-hotfix", "1.2.3", True),
        ("1.2.3", "rc-1.2.3", True),
        ("rc-1.2.3", "1.2.3", True),
        ("1.2.*", "1.2.3", True),
        ("1.2.3", "1.2.*", False),
        ("1.2.3", "0.2.3", False),
        ("1.2.3", "1.1.1", False),
        ("1.2.3", "1.2.4", False),
    ],
)
def test_is_compatible(constraint: str, version: str, expected: bool):
    assert expected == version_utils.is_compatible(
        version_utils.version_from_str(constraint),
        version_utils.version_from_str(version),
    )


###
# compare_version
###


@pytest.mark.parametrize(
    "lhs,rhs,expected",
    [
        ("1.2.3", "1.2.3", 0),
        ("1.2.3-hotfixa", "1.2.3-hotfixb", -1),
        ("1.2.3-hotfixb", "1.2.3-hotfixa", 1),
        ("1.2.3", "1.2.3-hotfix", 1),
        ("1.2.3-hotfix", "1.2.3", -1),
        ("1.2.*", "1.2.*", 0),
        ("rc-1.2.3", "rc-1.2.3", 0),
        ("rc-1.2.3", "rc-1.2.3-hotfix", 1),
        ("rc-1.2.3-hotfix", "rc-1.2.3", -1),
        ("2.1.1", "1.2.3", 1),
        ("1.2.3", "2.1.1", -1),
        ("1.3.2", "1.2.3", 1),
        ("1.2.3", "1.3.2", -1),
        ("1.2.4", "1.2.3", 1),
        ("1.2.3", "1.2.4", -1),
        ("1.2.3", "rc-1.2.3", 1),
        ("rc-1.2.3", "1.2.3", -1),
        ("1.2.3", "1.2.*", 1),
        ("1.2.*", "1.2.3", -1),
        ("rc-1.2.3", "rc-1.2.2", 1),
        ("rc-1.2.2", "rc-1.2.3", -1),
        ("rc-1.2.3", "1.2.2", -1),
        ("1.2.2", "rc-1.2.3", 1),
    ],
)
def test_compare_version(lhs: str, rhs: str, expected: int):
    assert expected == version_utils.compare_version(
        version_utils.version_from_str(lhs), version_utils.version_from_str(rhs)
    )


###
# sort_versions
###


def test_sort_version():
    assert [
        Version(3, 1, 4, None, True),
        Version(2, 0, 0, None, False),
        Version(3, 1, 3, "hotfix", False),
        Version(3, 1, 3, None, False),
        Version(3, 1, 4, None, False),
        Version(3, 2, 1, None, False),
    ] == version_utils.sort_versions(
        [
            Version(3, 1, 4, None, False),
            Version(2, 0, 0, None, False),
            Version(3, 1, 3, None, False),
            Version(3, 2, 1, None, False),
            Version(3, 1, 4, None, True),
            Version(3, 1, 3, "hotfix", False),
        ]
    )
