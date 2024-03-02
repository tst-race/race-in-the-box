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

""" RiB /api/operations router """

# Python Library Imports
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState

# Local Python Library Imports
import rib.restapi.crud.operations as crud
from rib.restapi.dependencies import get_db
from rib.restapi.internal.operations_queue import operations_queue
from rib.restapi.internal.operations_websockets import operations_websockets
from rib.restapi.models.operations import DbOperation, OperationState
from rib.restapi.schemas.operations import (
    OperationLogs,
    OperationQueuedResult,
    OperationsQueuePage,
    QueuedOperation,
    StateChangeRequest,
)

router = APIRouter(
    prefix="/api/operations",
    tags=["Operations"],
    responses={404: {"description": "Not found"}},
)


@router.get("", response_model=OperationsQueuePage)
def get_operations(
    page: int = 1,
    size: int = 20,
    target: str = None,
    db_session: Session = Depends(get_db),
):
    """Get paged operations in the queue"""
    return {
        "operations": crud.get_operations(
            db_session,
            offset=(page - 1) * size,
            limit=size,
            target=target,
        ),
        "page": page,
        "size": size,
        "total": crud.get_operations_count(db_session, target=target),
    }


@router.delete("", status_code=204)
def delete_operations(db_session: Session = Depends(get_db)):
    """Delete non-running operations from the queue"""
    crud.delete_non_running_operations(db_session)


@router.websocket("/ws")
async def get_operations_websocket(websocket: WebSocket):
    """Obtain a websocket for operations queue updates"""
    await websocket.accept()
    queue = await operations_websockets.subscribe_to_status_updates()

    async def send_updates():
        while websocket.client_state == WebSocketState.CONNECTED:
            update = await queue.async_q.get()
            if update.get("shutdown"):
                break
            await websocket.send_json(update)

    # Run an async task to receive from the socket, this will wake up when the client
    # disconnects or the server is reloaded, so we can send an item into the queue to
    # wake up and exit out of the send_updates task.
    async def receive():
        while websocket.client_state == WebSocketState.CONNECTED:
            await websocket.receive()
        await queue.async_q.put({"shutdown": True})

    await asyncio.gather(send_updates(), receive())
    await operations_websockets.unsubscribe_from_status_updates(queue)
    queue.close()
    await queue.wait_closed()


@router.get("/{operation_id}", response_model=QueuedOperation)
def get_operation(operation_id: int, db_session: Session = Depends(get_db)):
    """Get queued operation"""
    db_operation = crud.get_operation(db_session, operation_id=operation_id)
    if db_operation is None:
        raise HTTPException(status_code=404, detail="Operation not found")
    return db_operation


@router.websocket("/{operation_id}/ws")
async def get_operation_websocket(
    operation_id: int, websocket: WebSocket, db_session: Session = Depends(get_db)
):
    """Obtain a websocket for a given operation"""
    await websocket.accept()
    queue = await operations_websockets.subscribe_to_operation(operation_id)

    async def send_updates():
        # Send all the logs prior to this connection
        total = crud.get_operation_logs_count(db_session, operation_id=operation_id)
        offset = 0
        while offset < total:
            lines = crud.get_operation_logs(
                db_session, operation_id=operation_id, offset=offset, limit=100
            )
            await websocket.send_json(jsonable_encoder({"lines": lines}))
            offset += len(lines)

        while websocket.client_state == WebSocketState.CONNECTED:
            update = await queue.async_q.get()
            if update.get("complete"):
                break
            await websocket.send_json(update)

    # Run an async task to receive from the socket, this will wake up when the client
    # disconnects or the server is reloaded, so we can send an item into the queue to
    # wake up and exit out of the send_updates task.
    async def receive():
        while websocket.client_state == WebSocketState.CONNECTED:
            await websocket.receive()
        await queue.async_q.put({"complete": True})

    await asyncio.gather(send_updates(), receive())
    await operations_websockets.unsubscribe_from_operation(operation_id, queue)
    queue.close()
    await queue.wait_closed()


@router.get("/{operation_id}/logs", response_model=OperationLogs)
def get_operation_logs(
    operation_id: int,
    offset: int = 0,
    limit: int = 1000,
    db_session: Session = Depends(get_db),
):
    """Get logs from an executed operation"""
    return {
        "lines": crud.get_operation_logs(
            db_session, operation_id=operation_id, offset=offset, limit=limit
        ),
        "offset": offset,
        "limit": limit,
        "total": crud.get_operation_logs_count(db_session, operation_id=operation_id),
    }


@router.put("/{operation_id}/state")
def change_state(
    operation_id: int,
    request: StateChangeRequest,
    db_session: Session = Depends(get_db),
):
    """Change state of a queued operation"""
    if request.state.lower() != "cancelled":
        raise HTTPException(
            status_code=400, detail="Invalid state, only allowed state is 'cancelled'"
        )
    db_operation = crud.get_operation(db_session, operation_id=operation_id)
    if db_operation is None:
        raise HTTPException(status_code=404, detail="Operation not found")
    if db_operation.state != OperationState.PENDING:
        raise HTTPException(
            status_code=422, detail="Operation cannot be modified, it is not pending"
        )
    db_operation.state = OperationState.CANCELLED
    db_session.commit()


@router.post(
    "/{operation_id}/retry", status_code=201, response_model=OperationQueuedResult
)
def retry_operation(operation_id: int, db_session: Session = Depends(get_db)):
    """Retry an operation"""
    orig_operation = crud.get_operation(db_session, operation_id=operation_id)
    if orig_operation is None:
        raise HTTPException(status_code=404, detail="Operation not found")
    new_operation = crud.create_operation(
        db_session,
        operation=DbOperation(
            name=orig_operation.name,
            requestMethod=orig_operation.requestMethod,
            requestPath=orig_operation.requestPath,
            requestQuery=orig_operation.requestQuery,
            requestBody=orig_operation.requestBody,
            postedTime=datetime.now(),
            target=orig_operation.target,
            function=orig_operation.function,
            args=orig_operation.args,
            state=OperationState.PENDING,
        ),
    )
    operations_queue.add(new_operation.id)
    return {"id": new_operation.id}
