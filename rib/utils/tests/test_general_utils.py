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
        Test File for general_utils.py
"""

# Python Library Imports
import os
import pathlib
import pytest
import sys
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, patch

# Local Library Imports
from rib.utils import error_utils, general_utils


###
# Fixtures / Mocks
###


def _get_test_file_path(file_name: str) -> str:
    """
    Test File Path
    """

    return f"{os.path.join(os.path.dirname(__file__))}/files/{file_name}"


###
# Tests
###


###
# get_current_time
###


def test_get_current_time():
    general_utils.datetime = MagicMock()
    general_utils.datetime.now = MagicMock(
        return_value=datetime(2022, 1, 3, 11, 22, 33)
    )
    assert general_utils.get_current_time() == "2022-01-03T11:22:33"


###
# load_file_into_memory
###


def test_load_file_into_memory_reads_json() -> int:
    """
    TODO
    """

    bytes_file = _get_test_file_path("test.json")
    data = general_utils.load_file_into_memory(bytes_file, "json")

    assert type(data) is dict
    assert len(data.keys()) == 1
    assert len(data[list(data.keys())[0]].keys()) == 2


def test_load_file_into_memory_reads_yaml_list() -> int:
    """
    TODO
    """

    bytes_file = _get_test_file_path("test.list.yml")
    data = general_utils.load_file_into_memory(bytes_file, "yaml")

    assert type(data) is list
    assert len(data) == 2


def test_load_file_into_memory_reads_yaml_dict() -> int:
    """
    TODO
    """

    bytes_file = _get_test_file_path("test.dict.yml")
    data = general_utils.load_file_into_memory(bytes_file, "yaml")

    assert type(data) is dict
    assert len(data.keys()) == 2


def test_load_file_into_memory_reads_bytes() -> int:
    """
    TODO
    """

    bytes_file = _get_test_file_path("test.bytes")
    data = general_utils.load_file_into_memory(bytes_file, "bytes")

    assert type(data) is bytes
    assert len(data) == 256


def test_load_file_into_memory_reads_string() -> int:
    """
    TODO
    """

    bytes_file = _get_test_file_path("test.txt")
    data = general_utils.load_file_into_memory(bytes_file, "string")

    assert type(data) is str
    assert len(data) == 787


###
# write_file_into_memory
###


def test_write_file_into_memory_writes_json(tmp_path: pathlib.PosixPath) -> int:
    """
    Purpose:
        Test that JSONs are written properly
    Args:
        tmp_path: a temporary
    """

    example_json_file = tmp_path / "json"
    example_json = {}

    # Write File
    general_utils.write_data_to_file(
        str(example_json_file), example_json, data_format="json", overwrite=False
    )

    # Confirm json written
    assert example_json_file.read_text() == "{}"

    # Write File again with overwrite
    general_utils.write_data_to_file(
        str(example_json_file), example_json, data_format="json", overwrite=True
    )

    # Confirm json written again
    assert example_json_file.read_text() == "{}"

    # Confirm overwrite not being set with an already set file fails
    with pytest.raises(error_utils.RIB006):
        # Write File
        general_utils.write_data_to_file(
            str(example_json_file), example_json, data_format="json", overwrite=False
        )


def test_write_file_into_memory_writes_bytes(tmp_path: pathlib.PosixPath) -> int:
    """
    Purpose:
        Test that Bytes are written properly
    Args:
        tmp_path: a temporary
    """

    example_bytes_file = tmp_path / "bytes"
    example_bytes = bytes("test", "utf-8")

    # Write File
    general_utils.write_data_to_file(
        str(example_bytes_file), example_bytes, data_format="bytes", overwrite=False
    )

    # Confirm bytes written
    assert example_bytes_file.read_bytes() == example_bytes

    # Write File again with overwrite
    general_utils.write_data_to_file(
        str(example_bytes_file), example_bytes, data_format="bytes", overwrite=True
    )

    # Confirm bytes written again
    assert example_bytes_file.read_bytes() == example_bytes

    # Confirm overwrite not being set with an already set file fails
    with pytest.raises(error_utils.RIB006):
        # Write File
        general_utils.write_data_to_file(
            str(example_bytes_file), example_bytes, data_format="bytes", overwrite=False
        )


def test_write_file_into_memory_writes_string(tmp_path: pathlib.PosixPath) -> int:
    """
    Purpose:
        Test that Strings are written properly
    Args:
        tmp_path: a temporary
    """

    example_string_file = tmp_path / "string"
    example_string = "test"

    # Write File
    general_utils.write_data_to_file(
        str(example_string_file), example_string, data_format="string", overwrite=False
    )

    # Confirm string written
    assert example_string_file.read_text() == example_string

    # Write File again with overwrite
    general_utils.write_data_to_file(
        str(example_string_file), example_string, data_format="string", overwrite=True
    )

    # Confirm string written again
    assert example_string_file.read_text() == example_string

    # Confirm overwrite not being set with an already set file fails
    with pytest.raises(error_utils.RIB006):
        # Write File
        general_utils.write_data_to_file(
            str(example_string_file),
            example_string,
            data_format="string",
            overwrite=False,
        )


def test_write_file_into_memory_writes_yaml(tmp_path: pathlib.PosixPath) -> int:
    """
    Purpose:
        Test that YAML are written properly
    Args:
        tmp_path: a temporary
    """

    example_yaml_file = tmp_path / "yaml"
    example_yaml = {}

    # Write File
    general_utils.write_data_to_file(
        str(example_yaml_file), example_yaml, data_format="yaml", overwrite=False
    )

    # Confirm yaml written
    assert example_yaml_file.read_text() == "{}\n"

    # Write File again with overwrite
    general_utils.write_data_to_file(
        str(example_yaml_file), example_yaml, data_format="yaml", overwrite=True
    )

    # Confirm yaml written again
    assert example_yaml_file.read_text() == "{}\n"

    # Confirm overwrite not being set with an already set file fails
    with pytest.raises(error_utils.RIB006):
        # Write File
        general_utils.write_data_to_file(
            str(example_yaml_file), example_yaml, data_format="yaml", overwrite=False
        )


###
# get_contents_of_dir
###


def test_get_files_in_dir(tmp_path: pathlib.PosixPath) -> int:
    """
    Purpose:
        Test getting files in a dir with a given extension
    Args:
        tmp_path: a temporary dir
    """

    example_extension = "py"
    example_filenames = [
        f"a.{example_extension}",
        f"b.{example_extension}",
        f"c.{example_extension}",
    ]
    example_full_filenames = [
        f"{tmp_path}/{example_filename}" for example_filename in example_filenames
    ]
    example_files = []
    for example_filename in example_filenames:
        temp_file = tmp_path / example_filename
        temp_file.write_text("test")
        example_files.append(temp_file)

    # Get files in temp dir
    files_in_dir = general_utils.get_contents_of_dir(
        str(tmp_path), full_path=False, extension=example_extension
    )

    # Confirm json written
    assert files_in_dir == example_filenames

    # Get files in temp dir
    full_files_in_dir = general_utils.get_contents_of_dir(
        str(tmp_path), full_path=True, extension=example_extension
    )

    # Confirm json written
    assert full_files_in_dir == example_full_filenames


###
# copy_dir_file
###


# TODO


###
# remove_dir_file
###


# TODO


###
# make_directory
###


# TODO


###
# guess_port_by_protocol
###


def test_guess_port_by_protocol() -> int:
    """
    Purpose:
        Test getting known port numbers
    Args:
        N/A
    """

    # Confirm ports
    assert general_utils.guess_port_by_protocol("ssh") == 22
    assert general_utils.guess_port_by_protocol("http") == 80
    assert general_utils.guess_port_by_protocol("https") == 443
    assert general_utils.guess_port_by_protocol("something_unknown") == None


###
# format_yaml_template
###


# TODO


###
# get_all_subclasses
###


def test_get_all_subclasses() -> int:
    """
    Purpose:
        Test get_all_subclasses returns subclasses
    Args
        N/A
    """

    class ExampleParent:
        def __init__(self):
            pass

    class ExampleChild1(ExampleParent):
        def __init__(self):
            pass

    class ExampleChild2(ExampleParent):
        def __init__(self):
            pass

    expected_subclasses = set()
    expected_subclasses.add(ExampleChild1)
    expected_subclasses.add(ExampleChild2)

    assert general_utils.get_all_subclasses(ExampleParent) == expected_subclasses


###
# zip a directory
###


@patch("rib.utils.general_utils.get_contents_of_dir")
@patch("os.walk")
@patch("os.path.isdir")
@patch("os.path.isfile")
@patch("zipfile.ZipFile")
def test_zip_directory(
    mock_zip, mock_isfile, mock_isdir, mock_os_walk, mock_get_contents_of_dir
) -> int:
    """
    Purpose:
        Test zipping up a directory
    Args:
        N/A
    """

    call_list = []

    class mock_zip_class:
        def write(self, filename, compress_type, arcname):
            call_list.append(filename)

        def close(self):
            pass

        filename = ""

    def mock_zipfile_init(filename, _):
        return mock_zip_class()

    mock_zip.side_effect = mock_zipfile_init

    def mock_is_dir_side_effect_func(path):
        # only return true for one platform to simplify test
        if "linux-client" in path:
            return True
        return False

    mock_isdir.side_effect = mock_is_dir_side_effect_func
    mock_get_contents_of_dir.return_value = ["plugin_1"]
    mock_isfile.return_value = (
        False  # Setting false to test case where plugin is a directory
    )

    top_level_dir = "top_dir", "sub_dir", ["top_level_file"]
    subdir = "top_dir/sub_dir", None, ["second_level_file"]
    mock_os_walk.return_value = [top_level_dir, subdir]
    general_utils.zip_directory(dir_path="local/path")

    assert call_list == [
        "top_dir",
        "top_dir/top_level_file",
        "top_dir/sub_dir",
        "top_dir/sub_dir/second_level_file",
    ]
