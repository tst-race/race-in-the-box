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

""" Operations WebSocket connection manager """

# Python Library Imports
import logging
from janus import Queue
from typing import Any, Dict, List


logger = logging.getLogger(__name__)


WebSocketQueue = Queue[Dict[str, Any]]


class OperationsWebSockets:
    """Manager of WebSocket connections for operations queue updates & live operation updates"""

    def __init__(self):
        """Initialize the internal data structures"""
        self.queues_by_id: Dict[int, List[WebSocketQueue]] = {}
        self.status_update_queues: List[WebSocketQueue] = []

    async def subscribe_to_operation(self, operation_id: int) -> WebSocketQueue:
        """Creates a queue from which to receive live operation updates"""
        self.queues_by_id.setdefault(operation_id, [])
        queue = Queue()
        self.queues_by_id[operation_id].append(queue)
        return queue

    async def unsubscribe_from_operation(
        self, operation_id: int, queue: WebSocketQueue
    ):
        """Removes the given queue so it no longer receives live operation updates"""
        if operation_id in self.queues_by_id:
            self.queues_by_id[operation_id].remove(queue)
            if len(self.queues_by_id[operation_id]) == 0:
                del self.queues_by_id[operation_id]

    def broadcast_for_operation(self, operation_id: int, update: Dict[str, Any]):
        """Sends the given update to all subscribers for this operation"""
        if operation_id in self.queues_by_id:
            for queue in self.queues_by_id[operation_id]:
                queue.sync_q.put_nowait(update)

    async def subscribe_to_status_updates(self) -> WebSocketQueue:
        """Creates a queue from which to receive queue updates"""
        queue = Queue()
        self.status_update_queues.append(queue)
        return queue

    async def unsubscribe_from_status_updates(self, queue: WebSocketQueue):
        """Removes the given queue so it no longer receives queue updates"""
        self.status_update_queues.remove(queue)

    def broadcast_status_update(self, update: Dict[str, Any]):
        """Sends the given update to all subscribers for the queue"""
        for queue in self.status_update_queues:
            queue.sync_q.put_nowait(update)


operations_websockets = OperationsWebSockets()
