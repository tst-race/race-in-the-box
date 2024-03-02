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

""" Operations Queue Executor """

# Python Library Imports
import importlib
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.orm import Session
from typing import IO, List, Tuple

# Local Python Library Imports
from rib.restapi.crud.operations import (
    create_operation_log,
    get_operation,
    get_dangling_operations,
)
from rib.restapi.internal.database import SessionLocal
from rib.restapi.internal.operations_websockets import operations_websockets
from rib.restapi.models.operations import (
    DbOperationLogLine,
    LogLineLevel,
    LogLineSource,
    OperationState,
)
from rib.utils import error_utils, log_utils


logger = logging.getLogger(__name__)


def split_function(function: str) -> Tuple[str, str]:
    """Split the full name of a python function into the module and function names"""
    parts = function.split(".")
    return (".".join(parts[0:-1]), parts[-1])


def get_log_level(levelno: int) -> LogLineLevel:
    """Convert the logging level integer into a log line level enum"""
    if levelno == logging.CRITICAL:
        return LogLineLevel.CRITICAL
    if levelno == logging.ERROR:
        return LogLineLevel.ERROR
    if levelno == logging.WARNING:
        return LogLineLevel.WARNING
    if levelno == logging.INFO:
        return LogLineLevel.INFO
    if levelno == logging.DEBUG:
        return LogLineLevel.DEBUG
    if levelno == log_utils.TRACE:
        return LogLineLevel.TRACE
    return LogLineLevel.NOTSET


def broadcast_logs(operation_id: int, log_lines: List[DbOperationLogLine]):
    """Send the given log lines to all current WebSocket subscribers"""
    operations_websockets.broadcast_for_operation(
        operation_id, jsonable_encoder({"lines": log_lines})
    )


def broadcast_state(operation_id: int, name: str, state: OperationState):
    """Send the given queue update to all current WebSocket subscribers"""
    operations_websockets.broadcast_status_update(
        jsonable_encoder({"id": operation_id, "name": name, "state": state})
    )


class DatabaseLogHandler(logging.Handler):
    """Custom logging handler to create database records for each logging record"""

    def __init__(self, operation_id: int):
        super().__init__(level=log_utils.TRACE)
        self.operation_id = operation_id

    def emit(self, record: logging.LogRecord) -> None:
        if "websockets" in record.pathname:
            return
        try:
            db_session = SessionLocal()
            log = create_operation_log(
                db_session,
                DbOperationLogLine(
                    operation_id=self.operation_id,
                    source=LogLineSource.LOG,
                    logLevel=get_log_level(record.levelno),
                    text=record.getMessage(),
                    time=datetime.fromtimestamp(record.created),
                ),
            )
        finally:
            db_session.close()

        broadcast_logs(
            self.operation_id,
            [log],
        )


class StreamCapture:
    """Stream-like object to record all written output as database records"""

    def __init__(
        self,
        source: LogLineSource,
        level: LogLineLevel,
        operation_id: int,
        wrapped: IO,
    ):
        self.source = source
        self.level = level
        self.operation_id = operation_id
        self.wrapped = wrapped

    def write(self, message: str):
        """Record each non-empty line as a database record"""
        now = datetime.now()
        self.wrapped.write(message)

        try:
            db_session = SessionLocal()
            lines: List[DbOperationLogLine] = []
            for line in message.rstrip().splitlines():
                log = create_operation_log(
                    db_session,
                    DbOperationLogLine(
                        operation_id=self.operation_id,
                        source=self.source,
                        logLevel=self.level,
                        text=line.rstrip(),
                        time=now,
                    ),
                )
                lines.append(log)
        finally:
            db_session.close()

        if lines:
            broadcast_logs(self.operation_id, lines)

    def flush(self):
        """Flushes the wrapped stream"""
        self.wrapped.flush()


@contextmanager
def db_logger(operation_id: int) -> None:
    """Set up logging handlers and stream captures to record all output from the operation"""
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr
    handler = None
    try:
        handler = DatabaseLogHandler(operation_id)
        logging.root.addHandler(handler)
        sys.stdout = StreamCapture(
            wrapped=orig_stdout,
            source=LogLineSource.STDOUT,
            level=LogLineLevel.INFO,
            operation_id=operation_id,
        )
        sys.stderr = StreamCapture(
            wrapped=orig_stderr,
            source=LogLineSource.STDERR,
            level=LogLineLevel.ERROR,
            operation_id=operation_id,
        )
        yield
    finally:
        if handler:
            logging.root.removeHandler(handler)
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr


class OperationsQueue:
    """Operation execution queue, performing all executions in a background thread"""

    def __init__(self):
        logger.info("Starting operations queue executor")
        self.executor: ThreadPoolExecutor = None

    def start(self):
        """Create the executor and clean up dangling operations"""
        self.executor = ThreadPoolExecutor(max_workers=1)
        try:
            db_session = SessionLocal()
            # Clean up any dangling operations from a previous run
            for operation in get_dangling_operations(db_session):
                logger.debug(f"Marking dangling operation {operation.id} as aborted")
                operation.state = OperationState.ABORTED
        finally:
            db_session.commit()
            db_session.close()

    def shutdown(self):
        """Shutdown the executor"""
        self.executor.shutdown()

    def add(self, operation_id: int):
        """Add the given operation to the queue"""
        logger.debug(f"Scheduling operation {operation_id}")
        self.executor.submit(self._execute, operation_id)

    @staticmethod
    def _execute(operation_id: int):
        """Execute the given operation"""
        logger.debug(f"Task to execute operation {operation_id}")
        try:
            db_session = SessionLocal()
            operation = get_operation(db_session, operation_id)
            if operation is None:
                logger.warning(f"No operation found with ID {operation_id}")
                return

            if operation.state != OperationState.PENDING:
                logger.debug(
                    f"Task was scheduled to execute operation {operation.name}, "
                    f"but task has state {operation.state}, skipping operation"
                )
                return

            with db_logger(operation_id):
                logger.info(f"Executing operation {operation.name} (id {operation_id})")
                operation.startedTime = datetime.now()
                operation.state = OperationState.RUNNING
                db_session.commit()
                broadcast_state(operation_id, operation.name, operation.state)

                try:
                    (module_name, function_name) = split_function(operation.function)
                    module = importlib.import_module(module_name)
                    function = getattr(module, function_name)
                    kwargs = json.loads(operation.args)

                    function(**kwargs)

                    operation.state = OperationState.SUCCEEDED
                except ImportError as err:
                    logger.warning(f"Error importing {module_name}: {err}")
                    operation.state = OperationState.INVALID
                except KeyError as err:
                    logger.warning(f"Error locating {function_name}: {err}")
                    operation.state = OperationState.INVALID
                except TypeError as err:
                    logger.warning(f"Error invoking {function_name}: {err}")
                    operation.state = OperationState.INVALID
                except ValidationError as err:
                    logger.warning(f"Error validating {function_name} arguments: {err}")
                    operation.state = OperationState.INVALID
                except error_utils.RIB000 as err:
                    logger.warning(f"Operation failed: {str(err)}")
                    operation.state = OperationState.FAILED
                except Exception as err:
                    logger.warning(
                        f"Operation failed: {err} ({err.__class__.__name__})"
                    )
                    operation.state = OperationState.FAILED

                operation.stoppedTime = datetime.now()
                db_session.commit()
                logger.info(
                    f"Execution of operation {operation.name} (id {operation_id}) "
                    f"completed with status {operation.state}"
                )
        except Exception as err:
            logger.error(f"Error executing task {operation_id}: {err}")
        finally:
            # Tell operation subscribers that this job is finished
            operations_websockets.broadcast_for_operation(
                operation_id, {"complete": True, "state": operation.state}
            )
            broadcast_state(operation_id, operation.name, operation.state)
            db_session.close()


operations_queue = OperationsQueue()
