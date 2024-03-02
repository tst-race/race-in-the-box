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
    Utilities for uploading and downloading files from the orchestration
    file server
"""

# Python Library Imports
import logging
import requests
from typing import List

# Local Python Library Imports
from rib.utils import ssh_utils


###
# Globals
###

logger = logging.getLogger(__name__)


###
# Types
###


class FileServerClient:
    """Client for interacting with the orchestration file server"""

    remote_url: str

    def __init__(self, remote_url: str = "http://rib-file-server:8080") -> None:
        """
        Purpose:
            Initializes the file server client
        Args:
            remote_url: URL (hostname and port) of the file server
        Returns:
            N/A
        """
        self.remote_url = remote_url

    def delete_all(self) -> bool:
        """
        Purpose:
            Deletes all files in the file server
        Args:
            N/A
        Returns:
            True if deletion was successful
        """
        try:
            url = f"{self.remote_url}/clear"
            resp = requests.post(url)
            if resp.status_code != 200:
                logger.warning(f"Clear returned status code: {resp.status_code}")
                return False
            return True
        except Exception as err:
            logger.warning(f"Error executing clear: {err}")
            return False

    def delete_file(self, remote_file_name: str) -> bool:
        """
        Purpose:
            Deletes a file from the file server
        Args:
            remote_file_name: Name of the file to be deleted
        Returns:
            True if file was successfully deleted
        """
        try:
            url = f"{self.remote_url}/{remote_file_name}"
            with requests.delete(url) as resp:
                if resp.status_code != 200:
                    logger.warning(
                        f"Delete for {remote_file_name} returned status code: {resp.status_code}"
                    )
                    return False
            return True
        except Exception as err:
            logger.warning(f"Error executing delete for {remote_file_name}: {err}")
            return False

    def download_file(self, remote_file_name: str, local_file_path: str) -> bool:
        """
        Purpose:
            Downloads a file from the file server
        Args:
            remote_file_name: Name of the file to be downloaded
            local_file_path: Full path to the local file location to which to download
        Returns:
            True if file was successfully downloaded
        """
        url = f"{self.remote_url}/{remote_file_name}"
        with requests.get(url, stream=True) as resp:
            if resp.status_code != 200:
                logger.warning(
                    f"Download for {remote_file_name} returned status code: {resp.status_code}"
                )
                return False
            with open(local_file_path, "wb") as local_file:
                for chunk in resp.iter_content(chunk_size=8192):
                    local_file.write(chunk)
        return True

    def get_file_list(self) -> List[str]:
        """
        Purpose:
            Gets a list of all files in the file server
        Args:
            N/A
        Returns:
            List of files available in the file server
        """
        resp = requests.get(self.remote_url)
        if resp.status_code != 200:
            logger.warning(f"Get file listing returned status code: {resp.status_code}")
            return []
        return resp.json().get("files", [])

    def upload_file(self, local_file_path: str, timeout: int = 120) -> bool:
        """
        Purpose:
            Uploads a file to the file server.
        Args:
            local_file_path: Full path to the local file to be uploaded.
            timeout: Time in seconds to wait for upload request to complete.
        Returns:
            True if file was successfully uploaded, False on failure.
        """
        url = f"{self.remote_url}/upload"
        with open(local_file_path, "rb") as local_file:
            resp = requests.post(url, files={"file": local_file}, timeout=timeout)
        if resp.status_code != 200:
            logger.warning(
                f"Upload for {local_file_path} returned status code: {resp.status_code}"
            )
            return False
        return True

    def is_file_on_file_server(self, remote_file_name: str) -> bool:
        """
        Purpose:
            Checks if a file exists in the file server
        Args:
            remote_file_name: Name of the file to look for
        Returns:
            True if the file exists in the file server
        """
        with requests.get(self.remote_url) as resp:
            if resp.status_code != 200:
                return False
            if remote_file_name not in str(resp.content):
                return False
            return True
