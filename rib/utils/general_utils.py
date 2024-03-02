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
        Utils for General Activities (I.E. File I/O)
"""

# Python Library Imports
import distutils
from distutils import dir_util
import json
import os
import pathlib
import re
import shutil
import socket
import tarfile
import yaml
from datetime import datetime
import pytz
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, Optional, Set, Union
from yaml import Loader as YamlLoader
import zipfile


# Local Python Library Imports
from rib.utils import error_utils


###
# Date/time
###


def get_current_time() -> str:
    """
    Purpose:
        Return the current time as an ISO8601-formatted string
    Args:
        N/A
    Return:
        Current time string
    """
    return datetime.now().isoformat()


def get_current_utc_time() -> datetime:
    """
    Purpose:
        Return the current time in a format that allows for mocking in a unit test
    Args:
        N/A
    Return:
        Current datetime
    """
    return datetime.now(pytz.utc)


###
# Disk I/O
###


def load_file_into_memory(
    filename: str, data_format: str = "string"
) -> Union[Dict[str, Any], list, bytes, str]:
    """Open a file, read the contents, optionally parse the data depending on the format,
    and return it.

    Args:
        filename (str): The name of the file to open, read, and parse.Any
        data_format (str, optional): The format of the data: "json", "yaml", bytes", or "string". Defaults to "string".

    Raises:
        error_utils.RIB006: Failed to open or parse the files for some reason

    Returns:
        Union[Dict[str, Any], list, bytes, str]: The formatted contents of the file.
            Varies based on data format.
                "json" : dict representation of the json.
                "yaml" : dict, list, or some other representation of the yaml depending on the contents of the yaml file.
                "bytes" : bytes
                "string" : str contents of the file.
    """
    file_mode = "rb" if data_format == "bytes" else "r"

    try:
        with open(filename, file_mode) as file_obj:
            if data_format == "json":
                # return type is a dict.
                return json.load(file_obj)
            elif data_format == "yaml":
                # return type is a dict, list, or whatever the yaml file happens to contain.
                return yaml.load(file_obj.read(), Loader=YamlLoader)
            elif data_format == "bytes":
                # return type is bytes
                return file_obj.read()
            elif data_format == "string":
                # return type is str.
                return file_obj.read()
            else:
                raise error_utils.RIB001(f"Loading {data_format} Format Files")
    except Exception as load_err:
        raise error_utils.RIB006(
            f"Exception Loading File {filename}: {load_err}"
        ) from None


def write_data_to_file(
    filename: str, data: Any, data_format: str = "string", overwrite: bool = True
) -> None:
    """
    Purpose:
        Write given data to a specified file. format determined by
        data_format arg.

        Defaults to string and failing if the file already exists
    Args:
        filename: Filename to write to
        data: Data to write to file
        data_format: Format of data to write
        overwrite: whether or not to overwrite file if it already exists
    Return:
        N/A
    Raises:
        error_utils.RIB001: unsupported data_format
        error_utils.RIB006: Failed to write
    """

    if os.path.isfile(filename) and not overwrite:
        raise error_utils.RIB006(
            f"{filename} already exists and overwrite not set"
        ) from None

    file_mode = "wb" if data_format == "bytes" else "w"

    try:
        with open(filename, file_mode) as file_obj:
            if data_format == "json":
                json.dump(
                    data, file_obj, sort_keys=True, indent=2, separators=(",", ": ")
                )
            elif data_format == "yaml":
                file_obj.write(yaml.dump(data, default_flow_style=False))
            elif data_format == "bytes":
                file_obj.write(data)
            elif data_format == "string":
                file_obj.write(data)
            else:
                raise error_utils.RIB001(f"Writing {data_format} Format Files")
    except Exception as write_err:
        raise error_utils.RIB006(
            f"Exception Writing File {filename}: {write_err}"
        ) from None


###
# Filesystem Functions
###


def get_contents_of_dir(file_path, full_path=True, extension="", include_dirs=False):
    """
    Purpose:
        Get all files in a dir. If an extension is passed in, limit files of that type.
        If full path is True, return the full path to the file.
    Args:
        file_path (String): Path to check for files
        full_path (Boolean): Whether or not to return the path as part of the filenames
        extension (String): extension to limit results to
        include_dirs (Boolean): Whether or not to include directories
    Return:
        filename (List of Strings): List of found filenames and/or directories
    """

    return sorted(
        [
            f"{file_path}/{filename}" if full_path else filename
            for filename in os.listdir(file_path)
            if (
                (os.path.isfile(os.path.join(file_path, filename)) or include_dirs)
                and re.match(rf".*{extension}$", filename)
            )
        ]
    )


def copy_dir_file(src_path: str, dest_path: str, overwrite: bool = False) -> None:
    """
    Purpose:
        Copy a file or files. Set recursive to True to recursively copy and set
        overwrite to true to delete previous and overwrite with new.

        Note: with dirs, will delete the root dir instead of overwriting only
        present files to remove lingering files in the dest dir that have been erased
        in the source dir
    Args:
        src_path: source path to copy
        dest_path: destination to copy
        overwrite: whether or not to delete previous file if it exists or to fail if
            dest already exists
    Return:
        N/A
    """

    if not os.path.isdir(src_path) and not os.path.isfile(src_path):
        raise Exception(f"{src_path} does not exist")
    elif (os.path.isdir(dest_path) or os.path.isfile(dest_path)) and not overwrite:
        raise Exception(f"{dest_path} already exists and overwrite false")
    elif os.path.isdir(src_path):
        if os.path.isdir(dest_path):
            remove_dir_file(dest_path)
        shutil.copytree(src_path, dest_path)
    elif os.path.isfile(src_path):
        if os.path.isfile(dest_path):
            remove_dir_file(dest_path)
        shutil.copyfile(src_path, dest_path)


def remove_dir_file(obj_path: str) -> None:
    """
    Purpose:
        Remove a dir or file from disk
    Args:
        obj_path: path to file/dir on disk to remove
    Return:
        N/A
    Raises:
        Exception: If the dir/file does not exist
        Exception: If the delete fails
    """

    if not os.path.isdir(obj_path) and not os.path.isfile(obj_path):
        raise Exception(f"{obj_path} does not exist")
    elif os.path.isdir(obj_path):
        shutil.rmtree(obj_path)
    elif os.path.isfile(obj_path):
        os.remove(obj_path)


def make_directory(
    dir_path: str, create_parents: bool = True, ignore_exists: bool = False
) -> None:
    """
    Purpose:
        Make a dir. If create_parents exists, create parent directories
        to path. If ignore_exists is try, ignore dir exists failure
    Args:
        dir_path: directory to create
        create_parents: create parent directories to path
        ignore_exists: ignore if the dir already exists
    Return:
        N/A
    Raises:
        Exception: If creation fails
        Exception: If parent dir missing and create_parents is false
        Exception: If the dir already exists and ignore_exists false
    """

    pathlib.Path(dir_path).mkdir(parents=create_parents, exist_ok=ignore_exists)


def zip_directory(dir_path: str, output_file: str = "") -> None:
    """
    Purpose:
        Zip a directory
    Args:
        dir_path (str): directory to zip
        output_file (str): path to output zip to. Defaults to same name/location as dir_path
    Return:
        zip_file: full path to produced zip file
    """
    if not output_file:
        output_file = f'{dir_path}/../{dir_path.split("/")[-1]}.zip'

    zip_file = zipfile.ZipFile(
        output_file,
        "w",
    )
    if os.path.isfile(dir_path):
        zip_file.write(
            filename=dir_path,
            compress_type=zipfile.ZIP_DEFLATED,
            arcname=dir_path.split("/")[-1],
        )
    else:
        for dirname, subdirs, files in os.walk(dir_path):
            dir_arcname = dirname.split(dir_path)[-1]
            dir_arcname = f'{dir_path.split("/")[-1]}{dir_arcname}'
            zip_file.write(
                filename=dirname,
                compress_type=zipfile.ZIP_DEFLATED,
                arcname=dir_arcname,
            )
            for filename in files:
                file_arcname = dir_arcname + "/" + filename
                zip_file.write(
                    filename=f"{dirname}/{filename}",
                    compress_type=zipfile.ZIP_DEFLATED,
                    arcname=file_arcname,
                )
    zip_file.close()
    return zip_file.filename


def unzip_file(zip_file: str, destination: str) -> None:
    """
    Purpose:
        Unzip a zipfile
    Args:
        zip_file: zipfile to extract
        destination: location to extract to
    Return:
        N/A
    """

    with zipfile.ZipFile(zip_file, "r") as zip_ref:
        zip_ref.extractall(destination)


def tar_directory(dir_path: str, output_file: str, compression: str = "gz") -> None:
    """
    Purpose:
        Create a tar archive of the given input directory
    Args:
        dir_path: Path to directory to be included in the tar archive
        output_file: Path to tar archive file to be written
        compression: Optional, compression type (e.g., "gz", "bz2", "xz", or "")
    Return:
        N/A
    """
    with tarfile.open(output_file, mode=f"w:{compression}") as tar:
        for subdir in os.listdir(dir_path):
            tar.add(os.path.join(dir_path, subdir), arcname=subdir)


###
# Network
###


def guess_port_by_protocol(protocol: str) -> Optional[int]:
    """
    Purpose:
        Guess a port number from a specified protocol name. Will use a common protocol
        lookup mapping to see what port that protocol is usually found on.

        e.g. guess_port_by_protocol("ssh") == 22
    Args:
        protocol: Name of comon protocol
    Return:
        port_guess: Port number if one is found, if one is known
    """

    # Build Known Protocol Table
    protocol_table = {
        name[8:].lower(): num
        for name, num in vars(socket).items()
        if name.startswith("IPPROTO")
    }
    protocol_table["ssh"] = 22
    protocol_table["http"] = 80
    protocol_table["https"] = 443

    return protocol_table.get(protocol, None)


###
# JSON Functions
###


def pretty_print_json(obj: Any) -> str:
    """
    Purpose:
        Pretty-print formats the given object as JSON
    Args:
        obj: Object to be printed
    Return:
        Pretty-print formatted JSON string
    """
    return json.dumps(obj, default=str, indent=2, sort_keys=True)


###
# YAML Functions
###


def format_yaml_template(
    file_path: str, format_data: Mapping[str, Any] = None
) -> Dict[str, Any]:
    """
    Purpose:
        Open a yaml template file, format the contents with the provided data, and
            convert and return it as a dict.
    Args:
        file_path (str): The path of the template file.
        format_data (Mapping[str, Any], optional): The data used to format the template.
            Defaults to None.

    Returns:
        Dict[str, Any]: A dict representation of the formatted yaml template.
    """

    if not format_data:
        format_data = {}

    yml_as_string = load_file_into_memory(file_path, data_format="string")
    try:
        service_data = yml_as_string.format_map(format_data)  # type: ignore
    except Exception as err:
        raise err

    return yaml.load(service_data, Loader=YamlLoader)


class CustomDumper(yaml.SafeDumper):
    """YAML dumper to customize the output YAML"""

    def ignore_aliases(self, data: Any) -> bool:
        """Disables generation of anchors and aliases"""
        return True

    def represent_data(self, data: Any) -> yaml.Node:
        """
        Purpose:
            Augments the base behavior for representing objects in YAML output.

            If the object is an Enum, the string representation is used.
        Args:
            data: Object to be represented
        Return:
            YAML node
        """
        if isinstance(data, Enum):
            return super().represent_str(str(data))
        return super().represent_data(data)


def pretty_print_yaml(obj: Any) -> str:
    """
    Purpose:
        Pretty-print formats the given object as YAML
    Args:
        obj: Object to be printed
    Return:
        Pretty-print formatted YAML string
    """
    return yaml.dump(
        obj,
        default_flow_style=False,
        indent=2,
        sort_keys=True,
        width=10000,
        Dumper=CustomDumper,
    )


###
# Class Functions
###


def get_all_subclasses(cls: type) -> Set[type]:
    """
    Purpose:
        get all subclasses a passed in class
    Args:
        cls: the class to get all sub-classes of.
    Return:
        all_subclasses (set): Set of all subclasses of the given class
    Raises:
        N/A
    """

    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in get_all_subclasses(c)]
    )


class Subscriptable:
    """Mixin to add support for the subscript operator"""

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, item, value):
        if hasattr(self, item):
            setattr(self, item, value)


###
# Enum Functions
###


class PrettyEnum(Enum):
    """
    Purpose:
        Python Enum with pretty repr/str
    """

    # pylint: disable=E0213
    def _generate_next_value_(name, start, count, last_values) -> str:
        """Generate value for enum from the name"""

        return name

    def __repr__(self) -> str:
        """Official representation of the Enum"""
        return enum_to_str(self)

    def __str__(self) -> str:
        """Informal/Pretty representation of the Enum"""
        return enum_to_str(self)


def enum_to_str(enum_instance: Enum) -> str:
    """
    Purpose:
        Returns a more human-friendly version of the enum name
    Args:
        enum_instance: Instance of the enum to return the name of as a string
    Return:
        enum_name: Name of the enum in string form
    """

    return enum_instance.name.lower().replace("_", " ")


###
# Stringify Functions
###


def stringify_nodes(nodes: Optional[Iterable[str]], max_nodes: int = 5) -> str:
    """Stringify node names, specifically to be used for describing deployment actions"""

    if not nodes:
        return "all nodes"
    elif len(nodes) < max_nodes:
        return ", ".join(nodes)
    # More than max
    return f"{len(nodes)} nodes"
