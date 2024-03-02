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
        Utilities for getting networking information needed for RiB
"""

# Python Library Imports
import logging
import os
import requests
from typing import Any, Dict, Optional, Tuple

# Local Library Imports
# N/A


logger = logging.getLogger(__name__)


###
# IP Functions
###


def get_public_ip() -> str:
    """
    Purpose:
        Get the public ip for the user through a third party service (Amazon AWS)
    Args:
        N/A
    Return:
        public_ip_address (str): the user's public IP address
    Raises:
        Exception: If there is a mismatch between IP addresses found
    """

    try:
        ip_request = requests.get("https://checkip.amazonaws.com")

        if ip_request.status_code != 200:
            raise Exception(
                f"Could not get IP Address, need to manually set. Request status code: {ip_request.status_code}"
            ) from None

        return ip_request.text.strip("\n")
    except Exception as err:
        raise Exception(
            f"Could not get IP Address, need to manually set: {repr(err)}"
        ) from None


def get_lan_ip() -> str:
    """
    Purpose:
        Get the IP address of the current host on the local network
    Args:
        N/A
    Return:
        Local area network IP address
    """

    ip_addr = os.environ.get("HOST_LAN_IP_ADDRESS")
    if not ip_addr:
        raise Exception("Host IP address not set")
    return ip_addr


###
# Requests Functions
###


def download_file(
    remote_url: str,
    local_path: str,
    headers: Optional[Dict[str, Any]] = None,
    chunk_size: int = 8192,
) -> Tuple[bool, int]:
    """
    Purpose:
        Downloads a file from a remote server
    Args:
        remote_url: Remote URL for for the file to be downloaded
        local_path: Local location to which to write the downloaded file
        headers: Optional request headers
        chunk_size: Chunk size to use while iterating through stream
    Returns:
        Tuple of success boolean and reponse status code
    """

    logger.trace(f"Downloading {remote_url} to {local_path}")
    with requests.get(remote_url, headers=headers, stream=True) as response:
        if response.status_code != 200:
            return (False, response.status_code)
        with open(local_path, "wb") as local_file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                local_file.write(chunk)
        return (True, response.status_code)
