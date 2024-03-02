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

""" JSON file database abstraction """

# Python Library Imports
import os
from fastapi import HTTPException
from typing import Any, List

# Local Python Library Imports
from rib.utils import general_utils


class JsonFiles:
    """JSON-file based document storage"""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        general_utils.make_directory(base_dir, ignore_exists=True)

    def create(self, name: str, data: Any) -> None:
        """Create new entry"""

        file_path = f"{self.base_dir}/{name}.json"
        if os.path.exists(file_path):
            raise HTTPException(status_code=400)

        try:
            general_utils.write_data_to_file(file_path, data, "json")
        except Exception as err:
            raise HTTPException(
                status_code=500, detail=f"Failed to write JSON file: {err}"
            ) from None

    def get_all(self) -> List[str]:
        """Get list of all entries"""

        try:
            filenames = general_utils.get_contents_of_dir(
                file_path=self.base_dir,
                full_path=False,
                extension="json",
            )
            return [filename[0:-5] for filename in filenames]
        except Exception as err:
            raise HTTPException(
                status_code=500, detail=f"Failed to read directory: {err}"
            ) from None

    def get(self, name: str) -> Any:
        """Read entry"""

        file_path = f"{self.base_dir}/{name}.json"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404)

        try:
            return general_utils.load_file_into_memory(file_path, "json")
        except Exception as err:
            raise HTTPException(
                status_code=500, detail=f"Failed to read JSON file: {err}"
            ) from None

    def update(self, name: str, data: Any) -> None:
        """Update entry"""

        file_path = f"{self.base_dir}/{name}.json"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404)

        try:
            general_utils.write_data_to_file(file_path, data, "json")
        except Exception as err:
            raise HTTPException(
                status_code=500, detail=f"Failed to write JSON file: {err}"
            ) from None

    def remove(self, name: str) -> None:
        """Delete entry"""

        file_path = f"{self.base_dir}/{name}.json"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404)

        try:
            general_utils.remove_dir_file(file_path)
        except Exception as err:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete JSON file: {err}"
            ) from None
