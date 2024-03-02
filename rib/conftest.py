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
    pytest global fixtures

    This file has to exist in the root source directory for the project
    in order to automatically apply to all tests. It cannot be moved into
    a tests/ directory, or this file would have to be repeated in every
    tests/ directory.

    Without these global fixtures, every single test file would need to
    perform the same setup operations.
"""
import pytest

from rib.utils.log_utils import register_trace_log_level


@pytest.fixture(scope="session", autouse=True)
def setup_logging() -> None:
    register_trace_log_level()
