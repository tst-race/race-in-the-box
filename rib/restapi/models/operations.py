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

""" Operation database models """

# Python Library Imports
import enum
from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import backref, relationship

# Local Python Library Imports
from rib.restapi.internal.database import Base


class OperationState(enum.Enum):
    """State of an operation"""

    PENDING = "PENDING"
    CANCELLED = "CANCELLED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    INVALID = "INVALID"


class DbOperation(Base):
    """Database model for an operation"""

    __tablename__ = "operations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    requestMethod = Column(String, nullable=False)
    requestPath = Column(String, nullable=False)
    requestQuery = Column(String, nullable=False)
    requestBody = Column(String, nullable=False)
    postedTime = Column(DateTime, nullable=False)
    target = Column(String, nullable=False)
    function = Column(String, nullable=False)
    args = Column(String, nullable=False)
    state = Column(Enum(OperationState), nullable=False)
    startedTime = Column(DateTime)
    stoppedTime = Column(DateTime)

    logs = relationship(
        "DbOperationLogLine", cascade="all, delete, delete-orphan", passive_deletes=True
    )


class LogLineSource(enum.Enum):
    """Operation log line source"""

    STDOUT = "STDOUT"
    STDERR = "STDERR"
    LOG = "LOG"


class LogLineLevel(enum.Enum):
    """Operation log line level"""

    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    TRACE = "TRACE"
    NOTSET = "NOTSET"


class DbOperationLogLine(Base):
    """Database model for a captured operation log line"""

    __tablename__ = "operation_log_lines"

    id = Column(Integer, primary_key=True)
    operation_id = Column(
        Integer, ForeignKey("operations.id", ondelete="CASCADE"), nullable=False
    )
    source = Column(Enum(LogLineSource), nullable=False)
    logLevel = Column(Enum(LogLineLevel), nullable=False)
    text = Column(String, nullable=False)
    time = Column(DateTime, nullable=False)
