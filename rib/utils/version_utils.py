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
    Utilities for describing and comparing versions
"""

# Python Library Imports
import logging
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


logger = logging.getLogger(__name__)


###
# Classes
###


@dataclass
class Version:
    """Version information"""

    major: int
    minor: int
    patch: Optional[int]
    prerelease: Optional[str]
    rc: bool

    def __str__(self) -> str:
        """Version as a string"""
        return "{}{}.{}.{}{}".format(
            "" if not self.rc else "rc-",
            self.major,
            self.minor,
            "*" if self.patch == None else self.patch,
            "" if self.prerelease == None else self.prerelease,
        )

    def __eq__(self, other: Any) -> bool:
        """Equality comparison with other version"""
        if not isinstance(other, Version):
            return False
        if self.major != other.major:
            return False
        if self.minor != other.minor:
            return False
        if self.patch != other.patch:
            return False
        if self.prerelease != other.prerelease:
            return False
        if self.rc != other.rc:
            return False
        return True


class VersionParseError(Exception):
    """An error thrown due to an invalid version string"""


###
# Functions
###


def version_from_str(version: str) -> Version:
    """
    Purpose:
        Extract version information from the given version string
    Args:
        version: Version as a string
    Return:
        Version information
    """

    parts = version.split(".")
    if len(parts) != 3:
        raise VersionParseError(
            f"Bad version: wrong number of segments in version: {version}"
        )

    major = parts[0]
    rc = False
    if major.startswith("rc-"):
        major = major[3:]
        rc = True
    if not major.isnumeric():
        raise VersionParseError(f"Bad version: major version is not numeric: {version}")
    major = int(major)

    minor = parts[1]
    if not minor.isnumeric():
        raise VersionParseError(f"Bad version: minor version is not numeric: {version}")
    minor = int(minor)

    patch = None
    prerelease = None
    if len(parts) > 2:
        patch = parts[2]
        if "-" in patch:
            patch_parts = patch.split("-")
            patch = patch_parts[0]
            prerelease = "-".join(patch_parts[1:])
        if patch == "*":
            patch = None
    if patch != None:
        if not patch.isnumeric():
            raise VersionParseError(
                f"Bad version: patch version is not numeric: {version}"
            )
        patch = int(patch)

    return Version(major=major, minor=minor, patch=patch, prerelease=prerelease, rc=rc)


def is_compatible(constraint: Version, version: Version) -> bool:
    """
    Purpose:
        Check if the given version is compatible with the specified constraining version
    Args:
        constraint: Constraining version
        version: Version to be checked for compatibility with the constraining version
    Return:
        True if version is compatible with the constraining version
    """
    if constraint.major != version.major:
        return False
    if constraint.minor != version.minor:
        return False
    if constraint.patch != None:
        if version.patch == None:
            return False
        if version.patch > constraint.patch:
            return False
    return True


def to_comparable_tuple(version: Version) -> Tuple[int, int, int, bool]:
    """
    Purpose:
        Creates a tuple out of the given version info such that the tuple can be used directly
        in comparison statements
        (e.g., `if to_comparable_tuple(version1) < to_comparable_tuple(version2):`)

        Because of how Python handles tuple comparisons, a version will be considered greater than
        another based on the following order of evaluation:
        - by major version, then
        - by minor version, then
        - by patch version, then
        - non-RC versions are greater than RC versions
    Args:
        version: Version info
    Return:
        Tuple that can be used in comparison statements
    """
    return (
        not version.rc,  # False < True, and we want rc < not-rc so have to invert
        version.major,
        version.minor,
        version.patch if version.patch != None else -1,
        # '' < 'prerelease', and we want 'prerelease' < '' so use 'z's as lexicographically highest alphanumeric character
        version.prerelease if version.prerelease else "zzzz",
    )


def compare_version(lhs: Version, rhs: Version) -> int:
    """
    Purpose:
        Compare two versions
    Args:
        lhs: First version to compare
        rhs: Second version to compare
    Return:
        1 if the lhs version is newer (greater) than the rhs version
        -1 if the lhs version is older (lesser) than the rhs version
        0 if the lhs version is equivalent to the rhs version
    """
    lhs_tuple = to_comparable_tuple(lhs)
    rhs_tuple = to_comparable_tuple(rhs)
    if lhs_tuple > rhs_tuple:
        return 1
    if lhs_tuple < rhs_tuple:
        return -1
    return 0


def sort_versions(versions: List[Version]) -> List[Version]:
    """
    Purpose:
        Sort the given list of versions using semantic version comparison
    Args:
        versions: List of versions
    Return:
        Sorted list of versions
    """
    return sorted(versions, key=to_comparable_tuple)
