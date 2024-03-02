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

""" Messaging API schemas """

# Python Library Imports
from pydantic import BaseModel
from typing import Any, List, Optional

from rib.utils.elasticsearch_utils import (
    MessageTraceUi,
)

# Operation Payloads


class MessagesSingle(BaseModel):
    message: MessageTraceUi


class MessagesList(BaseModel):
    messages: List[MessageTraceUi]


class MessagesReport(MessagesList):
    rib_mode: str
    deployment_name: str


class MessagesSubsetReport(MessagesReport):
    search_after_vals: List[Any]
    has_more_pages: bool


class MessageSendAutoParams(BaseModel):
    message_period: int = 0
    message_quantity: int
    message_size: int
    recipient: Optional[str]
    sender: Optional[str]
    test_id: str
    network_manager_bypass_route: Optional[str]
    verify: bool = False
    timeout: Optional[int] = 0


class MessageSendManualParams(BaseModel):
    message_content: str
    recipient: Optional[str]
    sender: Optional[str]
    test_id: str
    network_manager_bypass_route: Optional[str]
    verify: bool = False
    timeout: Optional[int] = 0
