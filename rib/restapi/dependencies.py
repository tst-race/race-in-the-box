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

""" FastAPI dependencies """

# Python Library Imports
import json
import subprocess
from datetime import datetime
from fastapi import Depends, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

# Local Python Library Imports
from rib.restapi.crud.operations import create_operation
from rib.restapi.internal.database import SessionLocal
from rib.restapi.internal.operations_queue import operations_queue
from rib.restapi.models.operations import DbOperation, OperationState
from rib.restapi.schemas.operations import OperationQueuedResult
from rib.state.rib_state import RaceInTheBoxState
from rib.utils import log_utils, rib_utils


###
# Globals
###

RIB_CONFIG = rib_utils.load_race_global_configs()
log_utils.setup_logger(RIB_CONFIG, log_to_stdout=False)


###
# Dependencies
###


def get_rib_state():
    """Create RiB state object"""
    return RaceInTheBoxState(RIB_CONFIG)


def get_db():
    """Create local database session"""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


async def get_body(request: Request):
    """Get request body as a byte array"""
    return await request.body()


def get_queue_operation(
    request: Request, body=Depends(get_body), db_session: Session = Depends(get_db)
):
    """Get a function to place an operation onto the queue"""

    def queue_operation(
        target: str, name: str, function: str, **kwargs: Dict[str, Any]
    ) -> OperationQueuedResult:
        db_operation = create_operation(
            db_session,
            operation=DbOperation(
                name=name,
                requestMethod=request.method,
                requestPath=request.url.path,
                requestQuery=request.url.query,
                requestBody=body.decode("utf-8"),
                postedTime=datetime.now(),
                target=target,
                function=function,
                args=json.dumps(jsonable_encoder(kwargs)),
                state=OperationState.PENDING,
            ),
        )
        operations_queue.add(db_operation.id)
        return {"id": db_operation.id}

    return queue_operation


# TODO remove the following if we don't ever end up needing it


class CommandResult:
    """Result from running RiB command"""

    stdout: str
    stderr: str
    returncode: int

    @property
    def json(self):
        """Standard output parsed as JSON"""
        try:
            return json.loads(self.stdout)
        except Exception as err:
            raise HTTPException(
                status_code=500, detail=f"JSON parse error: {err}"
            ) from None


class RiBCli:
    """RiB CLI"""

    def run(
        self, *cmd: List[str], error_code: Optional[int] = None, error_prefix: str = ""
    ):
        """Run RiB command"""
        rib_cmd = ["rib"]
        rib_cmd.extend(cmd)
        proc = subprocess.Popen(
            rib_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        proc.wait()

        result = CommandResult()
        result.stdout = proc.stdout.read().decode()
        result.stderr = proc.stderr.read().decode()
        result.returncode = proc.returncode

        if error_code and result.returncode != 0:
            if error_prefix:
                error_prefix = f"{error_prefix}: "
            raise HTTPException(
                status_code=error_code, detail=f"{error_prefix}{result.stderr}"
            )

        return result
