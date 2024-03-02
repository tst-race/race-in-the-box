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

""" Operation API schemas """

# Python Library Imports
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional

# Local Python Library Imports
from rib.restapi.models.operations import LogLineLevel, LogLineSource, OperationState


class QueuedOperation(BaseModel):
    """Queued operation API schema"""

    id: int
    name: str
    requestMethod: str
    requestPath: str
    requestQuery: str
    requestBody: str
    postedTime: datetime
    target: str
    state: OperationState
    startedTime: Optional[datetime] = Field(..., nullable=True)
    stoppedTime: Optional[datetime] = Field(..., nullable=True)

    class Config:
        orm_mode = True


class OperationsQueuePage(BaseModel):
    """Single page of operations queue"""

    operations: List[QueuedOperation]
    page: int
    size: int
    total: int


class OperationLogLine(BaseModel):
    """A single log line from an executed operation"""

    source: LogLineSource
    logLevel: LogLineLevel
    text: str
    time: datetime

    class Config:
        orm_mode = True


class OperationLogs(BaseModel):
    """A subset of log lines from an executed operation"""

    lines: List[OperationLogLine]
    offset: int
    limit: int
    total: int


class LiveOperationLogsUpdate(BaseModel):
    """A subset of log lines from an executed operation broadcasted in real time"""

    lines: List[OperationLogLine]


class StateChangeRequest(BaseModel):
    """A request to change the state of an operation (i.e, cancel)"""

    state: str


class OperationQueuedResult(BaseModel):
    """The result of queueing an operation"""

    id: int


class OperationStateUpdate(BaseModel):
    """Update to an operation in the queue"""

    id: int
    state: OperationState
