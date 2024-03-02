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

""" RiB /api/deployments/{mode}/{name}/messaging/ router """

# Python Library Imports
from fastapi import APIRouter, Depends, Request

# Local Python Library Imports
from rib.utils import messaging_utils
from rib.utils import error_utils

from rib.restapi.dependencies import get_queue_operation

from rib.restapi.schemas.operations import OperationQueuedResult

from rib.restapi.schemas.messaging import (
    MessageSendAutoParams,
    MessageSendManualParams,
    MessagesSubsetReport,
)
from rib.restapi.routers.local_deployment import _operation_name

router = APIRouter(
    prefix="/api/deployments/{mode}/{name}/messages",
    tags=["Messaging"],
    responses={404: {"description": "{mode}/{name} Not found"}},
)


# Local class definitions

###
# Retrieval routes
###


@router.get("/list", response_model=MessagesSubsetReport)
def get_matching_messages(
    mode: str,
    name: str,
    request: Request,
):
    """Get matching subset of messages from deployment"""
    params = request.query_params

    if params.get("input_search_after_vals", None):
        input_search_after_vals = params.get("input_search_after_vals").split(",")
    else:
        input_search_after_vals = []

    if params.get("reverse_sort", "false") == "true":
        input_reverse_sort = True
    else:
        input_reverse_sort = False

    try:
        (
            new_search_after_vals,
            messages,
            has_more_pages,
        ) = messaging_utils.ui_get_matching_messages(
            rib_mode=mode,
            deployment_name=name,
            size=int(params.get("size", 50)),
            recipient=params.get("recipient", None),
            sender=params.get("sender", None),
            test_id=params.get("test_id", None),
            trace_id=params.get("trace_id", None),
            date_from=params.get("date_from", None),
            date_to=params.get("date_to", None),
            reverse_sort=input_reverse_sort,
            search_after_vals=input_search_after_vals,
        )
        return {
            "messages": messages,
            "rib_mode": mode,
            "deployment_name": name,
            "search_after_vals": new_search_after_vals,
            "has_more_pages": has_more_pages,
        }
    except:
        raise error_utils.RIB605(mode, name, "ui - get matching messages")


###
# Operation Routes
###


@router.post("/send-auto", response_model=OperationQueuedResult)
def send_auto(
    mode: str,
    name: str,
    data: MessageSendAutoParams,
    queue_operation=Depends(get_queue_operation),
):
    """Run a Send-Auto Operation over the RACE network"""

    return queue_operation(
        target=f"deployment:{mode}:{name}",
        name=_operation_name("Send Auto Messages with", data.sender or "", name),
        function="rib.restapi.operations.messaging.send_auto",
        deployment_name=name,
        deployment_mode=mode,
        data=data,
    )


@router.post("/send-manual", response_model=OperationQueuedResult)
def send_manual(
    mode: str,
    name: str,
    data: MessageSendManualParams,
    queue_operation=Depends(get_queue_operation),
):
    """Run a Send-Auto Operation over the RACE network"""

    return queue_operation(
        target=f"deployment:{mode}:{name}",
        name=_operation_name("Send Manual Messages between", data.sender or "", name),
        function="rib.restapi.operations.messaging.send_manual",
        deployment_name=name,
        deployment_mode=mode,
        data=data,
    )
