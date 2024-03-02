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

""" Local deployment operation functions """

# Python Library Imports
import os
import tempfile
import time
from fastapi.encoders import jsonable_encoder
from typing import Any, Dict

# Local Python Library Imports
from rib.deployment import RibLocalDeployment
from rib.utils import (
    testing_utils,
    error_utils,
)
from rib.restapi.schemas.messaging import (
    MessageSendAutoParams,
    MessageSendManualParams,
)


def send_auto(deployment_name: str, deployment_mode: str, data: Dict[str, Any]):
    """Send Auto message routine"""

    # in UI, timeout cannot be non-zero/exist without verify being true

    params = MessageSendAutoParams.parse_obj(data)

    # Getting instance of existing deployment
    deployment = RibLocalDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    # Give a non-named verify test a unique name
    if params.test_id == "" and params.verify:
        params.test_id = "V-" + str(time.time())

    # Initialize testing object to track verification testing
    test_result = testing_utils.TestResult(test_case="send_auto_messages")

    # Check if UI input needs to be adjusted
    if params.sender == "":
        params.sender = None
    if params.recipient == "":
        params.recipient = None
    if params.message_period == None:
        params.message_period = 0

    start_time = int(time.time() * 1000)

    # Updated send_message to return the recipient_sender_mapping
    returned_recipient_sender_mapping = deployment.send_message(
        message_type="auto",
        message_period=params.message_period,
        message_quantity=params.message_quantity,
        message_size=params.message_size,
        recipient=params.recipient,
        sender=params.sender,
        test_id=params.test_id,
        network_manager_bypass_route=params.network_manager_bypass_route,
    )

    if params.verify:
        # if specified, expecting timeout as num of seconds
        if not params.timeout:
            params.timeout = 30  # default

        result = testing_utils.evaluate_messages_test(
            elasticsearch_host_name=deployment.get_elasticsearch_hostname(),
            test_id=params.test_id,
            start_time=start_time,
            run_time=params.timeout,
            test_result=test_result,
            expected_message_count=params.message_quantity,
            recipient_sender_mapping=returned_recipient_sender_mapping,
            expected_message_size=params.message_size,
            range_name=deployment.get_range_name(),
        )

        # print the report and return the report status
        all_passed = testing_utils.print_single_test_case_report(result)

        if not all_passed:
            raise error_utils.RIB604(deployment_mode, deployment_name, "auto")


def send_manual(deployment_name: str, deployment_mode: str, data: Dict[str, Any]):
    """Send Manual message routine"""

    # in UI, timeout cannot be non-zero/exist without verify being true

    params = MessageSendManualParams.parse_obj(data)

    # Getting instance of existing deployment
    deployment = RibLocalDeployment.get_existing_deployment_or_fail(
        deployment_name, deployment_mode
    )

    # Give a non-named verify test a unique name
    if params.test_id == "" and params.verify:
        params.test_id = "V-" + str(time.time())

    # Initialize testing object to track verification testing
    test_result = testing_utils.TestResult(test_case="send_manual_messages")

    # Check if UI input needs to be adjusted
    if params.sender == "":
        params.sender = None
    if params.recipient == "":
        params.recipient = None

    # Updated send message to return the recipient sender mapping
    returned_recipient_sender_mapping = deployment.send_message(
        message_type="manual",
        message_content=params.message_content,
        recipient=params.recipient,
        sender=params.sender,
        test_id=params.test_id,
        network_manager_bypass_route=params.network_manager_bypass_route,
    )

    if params.verify:
        # if specified, expecting timeout as num of seconds
        if not params.timeout:
            params.timeout = 30  # default

        start_time = int(time.time() * 1000)

        # expected message count/quantity should be 1 in manual send mode
        # this is because message quantity refers to the number of messages along each paired edge,
        # not the total number of messages in the network
        message_quantity = 1

        result = testing_utils.evaluate_messages_test(
            elasticsearch_host_name=deployment.get_elasticsearch_hostname(),
            test_id=params.test_id,
            start_time=start_time,
            run_time=params.timeout,
            test_result=test_result,
            expected_message_count=message_quantity,
            recipient_sender_mapping=returned_recipient_sender_mapping,
            range_name=deployment.get_range_name(),
        )

        # print the report and return the report status
        all_passed = testing_utils.print_single_test_case_report(result)

        if not all_passed:
            raise error_utils.RIB604(deployment_mode, deployment_name, "manual")
