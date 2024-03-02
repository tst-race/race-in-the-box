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

""" Operation database CRUD functions """

# Python Library Imports
from sqlalchemy.orm import Session
from typing import List, Optional

# Local Python Library Imports
from rib.restapi.models.operations import (
    DbOperation,
    DbOperationLogLine,
    OperationState,
)


def get_operations_count(db_session: Session, target: str = None) -> int:
    """Get the total number of operations in the database"""
    query = db_session.query(DbOperation)

    if target:
        query = query.filter(DbOperation.target == target)

    return query.count()


def get_operations(
    db_session: Session, offset: int = 0, limit: int = 20, target: str = None
) -> List[DbOperation]:
    """Get operations from the database"""
    query = db_session.query(DbOperation)

    if target:
        query = query.filter(DbOperation.target == target)

    return (
        query.order_by(DbOperation.postedTime.desc()).offset(offset).limit(limit).all()
    )


def get_dangling_operations(db_session: Session) -> List[DbOperation]:
    """Get all operations with a state of PENDING or RUNNING"""
    return (
        db_session.query(DbOperation)
        .order_by(DbOperation.postedTime.asc())
        .filter(
            (DbOperation.state == OperationState.PENDING)
            | (DbOperation.state == OperationState.RUNNING)
        )
        .all()
    )


def get_operation(db_session: Session, operation_id: int) -> Optional[DbOperation]:
    """Get the specified operation from the database"""
    return db_session.query(DbOperation).filter(DbOperation.id == operation_id).first()


def create_operation(db_session: Session, operation: DbOperation) -> DbOperation:
    """Add the given operation to the database"""
    db_session.add(operation)
    db_session.commit()
    db_session.refresh(operation)
    return operation


def delete_non_running_operations(db_session: Session):
    """Delete operations that are not in a running state"""
    db_session.query(DbOperation).filter(
        DbOperation.state != OperationState.RUNNING
    ).delete()
    db_session.commit()


def get_operation_logs_count(db_session: Session, operation_id: int) -> int:
    """Get the total number of log lines for the specified operation"""
    return (
        db_session.query(DbOperationLogLine)
        .filter(DbOperationLogLine.operation_id == operation_id)
        .count()
    )


def get_operation_logs(
    db_session: Session, operation_id: int, offset: int = 0, limit: int = 1000
) -> List[DbOperationLogLine]:
    """Get log lines for the specified operation"""
    return (
        db_session.query(DbOperationLogLine)
        .filter(DbOperationLogLine.operation_id == operation_id)
        .order_by(DbOperationLogLine.time.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def create_operation_log(
    db_session: Session, line: DbOperationLogLine
) -> DbOperationLogLine:
    """Add the given operation log line to the database"""
    db_session.add(line)
    db_session.commit()
    db_session.refresh(line)
    return line
