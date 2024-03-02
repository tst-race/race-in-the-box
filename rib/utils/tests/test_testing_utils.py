#!/usr/bin/env python3

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

"""
Purpose:
    Test File for testing_utils.py
"""

# Python Library Imports
from enum import auto
import re
from typing import List
import pytest
from unittest import mock
from unittest.mock import MagicMock, Mock
from mock import patch

# Local Library Imports
from rib.utils import error_utils, general_utils, testing_utils, elasticsearch_utils


###
# Fixtures/Mocks
###


@pytest.fixture
def mock_default_test_config() -> None:
    """A default test config"""

    return testing_utils.TestConfig()


@pytest.fixture
def mock_nondefault_test_config() -> None:
    """A non-default test config"""

    return testing_utils.TestConfig(
        run_time=200,
        delay_start=5,
        delay_execute=5,
        is_running=True,
        network_manager_bypass=True,
        comms_channel="test",
        comms_channel_type="c2s",
        no_down=True,
    )


@pytest.fixture
def mock_default_test_case() -> None:
    """A default test case"""

    return testing_utils.TestCase(name="")


@pytest.fixture
def mock_nondefault_test_case() -> None:
    """A non-default test case"""

    return testing_utils.TestCase(name="manual_messages", settings={"x": True})


@pytest.fixture
def mock_default_test_result() -> None:
    """A default test result"""

    return testing_utils.TestResult(test_case="")


@pytest.fixture
def mock_nondefault_test_result() -> None:
    """A non-default test result"""

    return testing_utils.TestResult(
        test_case="manual_messages",
        total=2,
        passed=1,
        failed=1,
        failed_expectations=["test"],
    )


@pytest.fixture
def mock_local_x2x_deployment() -> None:
    """A mock deployment to test"""

    return MagicMock(
        client_personas=["race-client-00001", "race-client-00002"],
        server_personas=["race-server-00001", "race-server-00002"],
        personas=[
            "race-client-00001",
            "race-client-00002",
            "race-server-00001",
            "race-server-00002",
        ],
        clients={"personas": {"race-client-00001": 1, "race-client-00002": 2}},
        servers={"personas": {"race-server-00001": 1, "race-server-00002": 2}},
        rib_mode="local",
    )


###
# Test Functionality
###


######
# TestConfig
######


def test_TestConfig_defaults(mock_default_test_config) -> int:
    """
    Purpose:
        Test TestConfig works with defaults
    Args:
        N/A
    """

    assert mock_default_test_config.run_time == 240
    assert mock_default_test_config.delay_start == 15
    assert mock_default_test_config.delay_execute == 15
    assert mock_default_test_config.is_running == False
    assert mock_default_test_config.network_manager_bypass == False
    assert mock_default_test_config.comms_channel == None
    assert mock_default_test_config.comms_channel_type == None
    assert mock_default_test_config.no_down == False


def test_TestConfig_nondefaults(mock_nondefault_test_config) -> int:
    """
    Purpose:
        Test TestConfig works with non-defaults
    Args:
        N/A
    """

    assert mock_nondefault_test_config.run_time == 200
    assert mock_nondefault_test_config.delay_start == 5
    assert mock_nondefault_test_config.delay_execute == 5
    assert mock_nondefault_test_config.is_running == True
    assert mock_nondefault_test_config.network_manager_bypass == True
    assert mock_nondefault_test_config.comms_channel == "test"
    assert mock_nondefault_test_config.comms_channel_type == "c2s"
    assert mock_nondefault_test_config.no_down == True


######
# TestCase
######


def test_TestCase_defaults(mock_default_test_case) -> int:
    """
    Purpose:
        Test TestCase works with defaults
    Args:
        N/A
    """

    assert mock_default_test_case.name == ""
    assert mock_default_test_case.settings == {}


def test_TestCase_nondefaults(mock_nondefault_test_case) -> int:
    """
    Purpose:
        Test TestCase works with non-defaults
    Args:
        N/A
    """

    assert mock_nondefault_test_case.name == "manual_messages"
    assert mock_nondefault_test_case.settings == {"x": True}


######
# TestResult
######


def test_TestResult_defaults(mock_default_test_result) -> int:
    """
    Purpose:
        Test TestResult works with defaults
    Args:
        N/A
    """

    assert mock_default_test_result.test_case == ""
    assert mock_default_test_result.total == 0
    assert mock_default_test_result.passed == 0
    assert mock_default_test_result.failed == 0
    assert mock_default_test_result.failed_expectations == []


def test_TestResult_nondefaults(mock_nondefault_test_result) -> int:
    """
    Purpose:
        Test TestResult works with non-defaults
    Args:
        N/A
    """

    assert mock_nondefault_test_result.test_case == "manual_messages"
    assert mock_nondefault_test_result.total == 2
    assert mock_nondefault_test_result.passed == 1
    assert mock_nondefault_test_result.failed == 1
    assert mock_nondefault_test_result.failed_expectations == ["test"]


###
# RaceTest Attributes
###


def test_RaceTest_defaults(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest defaults are as expected with mock_local_x2x_deployment
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    assert race_test.clients == ["race-client-00001", "race-client-00002"]
    assert race_test.servers == ["race-server-00001", "race-server-00002"]
    assert race_test.recipient_sender_mapping == {
        "race-client-00002": ["race-client-00001"],
        "race-client-00001": ["race-client-00002"],
    }
    assert race_test.bootstrap_mapping == []
    assert race_test.bootstrap_verification_mapping == {}
    assert race_test.test_results == []
    assert race_test.deployment == mock_local_x2x_deployment

    assert len(race_test.test_cases) == 3
    assert race_test.test_config.run_time == 30


def test_RaceTest_failed(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest failed returns correctly
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)
    assert race_test.failed == False

    race_test.test_results.append(
        testing_utils.TestResult(
            test_case="failed", failed=1, failed_expectations=["x"]
        )
    )
    assert race_test.failed == True


def test_RaceTest_passed(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest passed returns correctly
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)
    assert race_test.passed == True

    race_test.test_results.append(
        testing_utils.TestResult(
            test_case="failed", failed=1, failed_expectations=["x"]
        )
    )
    assert race_test.passed == False


def test_RaceTest_total_failed(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest total_failed returns correctly
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)
    assert race_test.total_failed == 0

    race_test.test_results.append(
        testing_utils.TestResult(
            test_case="failed", failed=1, failed_expectations=["x"]
        )
    )
    assert race_test.total_failed == 1


def test_RaceTest_total_passed(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest total_passed returns correctly
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)
    assert race_test.total_passed == 0

    race_test.test_results.append(
        testing_utils.TestResult(
            test_case="failed", failed=1, failed_expectations=["x"]
        )
    )
    assert race_test.total_passed == 0

    race_test.test_results.append(
        testing_utils.TestResult(
            test_case="passed", failed=0, passed=3, failed_expectations=[]
        )
    )
    assert race_test.total_passed == 3


###
# RaceTest Export Functions
###


def test_RaceTest_export_plan_to_dict(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest export_plan_to_dict returns correctly
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)
    assert race_test.export_plan_to_dict() == {
        "clients": ["race-client-00001", "race-client-00002"],
        "servers": ["race-server-00001", "race-server-00002"],
        "recipient_sender_mapping": {
            "race-client-00002": ["race-client-00001"],
            "race-client-00001": ["race-client-00002"],
        },
        "bootstrap_mapping": [],
        "bootstrap_verification_mapping": {},
        "test_config": {
            "run_time": 30,
            "delay_start": 0,
            "delay_execute": 30,
            "delay_evaluation": 30,
            "evaluation_interval": 15,
            "is_running": False,
            "start_timeout": 300,
            "network_manager_bypass": False,
            "comms_channel": None,
            "comms_channel_type": None,
            "no_down": False,
        },
        "test_cases": [
            {"name": "bootstrap", "settings": {"enabled": True, "test_id": "BS-TEST"}},
            {
                "name": "manual_messages",
                "settings": {"enabled": True, "quantity": 1, "test_id": "MM-TEST"},
            },
            {
                "name": "auto_messages",
                "settings": {
                    "enabled": True,
                    "period": 10,
                    "quantity": 5,
                    "size": 140,
                    "test_id": "AM-TEST",
                },
            },
        ],
    }


def test_RaceTest_export_plan_to_str(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest export_plan_to_str returns correctly
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)
    assert (
        race_test.export_plan_to_str()
        == '"{\\"clients\\": [\\"race-client-00001\\", \\"race-client-00002\\"], \\"servers\\": [\\"race-server-00001\\", \\"race-server-00002\\"], \\"recipient_sender_mapping\\": {\\"race-client-00002\\": [\\"race-client-00001\\"], \\"race-client-00001\\": [\\"race-client-00002\\"]}, \\"bootstrap_mapping\\": [], \\"bootstrap_verification_mapping\\": {}, \\"test_config\\": {\\"run_time\\": 30, \\"start_timeout\\": 300, \\"delay_start\\": 0, \\"delay_execute\\": 30, \\"delay_evaluation\\": 30, \\"evaluation_interval\\": 15, \\"is_running\\": false, \\"network_manager_bypass\\": false, \\"comms_channel\\": null, \\"comms_channel_type\\": null, \\"no_down\\": false}, \\"test_cases\\": [{\\"name\\": \\"bootstrap\\", \\"settings\\": {\\"enabled\\": true, \\"test_id\\": \\"BS-TEST\\"}}, {\\"name\\": \\"manual_messages\\", \\"settings\\": {\\"enabled\\": true, \\"quantity\\": 1, \\"test_id\\": \\"MM-TEST\\"}}, {\\"name\\": \\"auto_messages\\", \\"settings\\": {\\"enabled\\": true, \\"period\\": 10, \\"quantity\\": 5, \\"size\\": 140, \\"test_id\\": \\"AM-TEST\\"}}]}"'
    )


###
# RaceTest generate_recipient_sender_mapping
###


def test_RaceTest_generate_recipient_sender_mapping_default(
    mock_local_x2x_deployment,
) -> int:
    """
    Purpose:
        Test RaceTest generate_recipient_sender_mapping returns correctly without
        network-manager-bypass
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    race_test.recipient_sender_mapping = {}
    race_test.generate_recipient_sender_mapping()

    assert race_test.recipient_sender_mapping == {
        "race-client-00002": ["race-client-00001"],
        "race-client-00001": ["race-client-00002"],
    }


def test_RaceTest_generate_recipient_sender_mapping_network_manager_bypass(
    mock_local_x2x_deployment,
) -> int:
    """
    Purpose:
        Test RaceTest generate_recipient_sender_mapping returns correctly with
        network-manager-bypass
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    # network-manager-bypass but no comms settings, invalid
    race_test.recipient_sender_mapping = {}
    race_test.test_config.network_manager_bypass = True
    with pytest.raises(Exception, match=r"network-manager-bypass"):
        race_test.generate_recipient_sender_mapping()
    assert race_test.recipient_sender_mapping == {}

    # c2s only
    race_test.recipient_sender_mapping = {}
    race_test.test_config.network_manager_bypass = True
    race_test.test_config.comms_channel_type = "c2s"
    race_test.generate_recipient_sender_mapping()
    assert race_test.recipient_sender_mapping == {
        "race-server-00001": ["race-client-00001", "race-client-00002"],
        "race-server-00002": ["race-client-00001", "race-client-00002"],
        "race-client-00001": ["race-server-00001", "race-server-00002"],
        "race-client-00002": ["race-server-00001", "race-server-00002"],
    }

    # s2s only
    race_test.recipient_sender_mapping = {}
    race_test.test_config.network_manager_bypass = True
    race_test.test_config.comms_channel_type = "s2s"
    race_test.generate_recipient_sender_mapping()
    assert race_test.recipient_sender_mapping == {
        "race-server-00002": ["race-server-00001"],
        "race-server-00001": ["race-server-00002"],
    }

    # both c2s and s2s
    race_test.recipient_sender_mapping = {}
    race_test.test_config.network_manager_bypass = True
    race_test.test_config.comms_channel_type = "all"
    race_test.generate_recipient_sender_mapping()
    assert race_test.recipient_sender_mapping == {
        "race-server-00001": ["race-client-00001", "race-client-00002"],
        "race-server-00002": ["race-client-00001", "race-client-00002"],
        "race-client-00001": ["race-server-00001", "race-server-00002"],
        "race-client-00002": ["race-server-00001", "race-server-00002"],
    }


###
# RaceTest validate
###


def test_RaceTest_validate_valid(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest validate properly validates the race_test: with a valid config
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)
    race_test.validate()
    assert True


@patch(
    "click.echo", MagicMock()
)  # Suppress log output, the mock isn't actually used for testing.
def test_RaceTest_validate_invalid_test_case(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest validate properly validates the race_test: invalid test case
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    # test invalid test case
    invalid_test_case = testing_utils.TestCase(name="bad")
    race_test.test_cases.append(invalid_test_case)
    with pytest.raises(error_utils.RIB600, match=r"Not a valid test case"):
        race_test.validate()


@patch("click.echo", MagicMock())
def test_RaceTest_validate_invalid_clients(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest validate properly validates the race_test: invalid client
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    # test invalid client
    race_test.clients.append("invalid-client")
    with pytest.raises(error_utils.RIB600, match=r"Clients"):
        race_test.validate()


@patch("click.echo", MagicMock())
def test_RaceTest_validate_invalid_servers(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest validate properly validates the race_test: invalid server
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    # test invalid server
    race_test.servers.append("invalid-server")
    with pytest.raises(error_utils.RIB600, match=r"Servers"):
        race_test.validate()


###
# RaceTest print_report
###


def test_RaceTest_print_report(
    mock_local_x2x_deployment, mock_nondefault_test_result
) -> int:
    """
    Purpose:
        Test RaceTest validate properly validates the race_test: invalid server
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    race_test.test_config.network_manager_bypass = True
    race_test.test_config.comms_channel = "test"
    race_test.test_config.comms_channel_type = "c2s"
    race_test.test_results.append(mock_nondefault_test_result)

    echo_output = ""
    with mock.patch("click.echo") as echo_mock:
        race_test.print_report()
        for call_args in echo_mock.call_args_list:
            echo_output += call_args.args[0]

    assert "deployment_name: " in echo_output
    assert "network manager plugin in deployment: " in echo_output
    assert "comms channels in deployment:" in echo_output
    assert "clients: ['race-client-00001', 'race-client-00002']" in echo_output
    assert "servers: ['race-server-00001', 'race-server-00002']" in echo_output
    assert "run_time: 30" in echo_output
    assert "delay_start: 0" in echo_output
    assert "delay_execute: 30" in echo_output
    assert "is_running: False" in echo_output
    assert "no_down: False" in echo_output
    assert "network_manager_bypass: True" in echo_output
    assert "comms_channel being tested: test" in echo_output
    assert "comms_channel_type being tested: c2s" in echo_output
    assert "manual_messages Test Results:" in echo_output
    assert " Tests Passed: 1" in echo_output
    assert " Tests Failed: 1" in echo_output
    assert "Failures:" in echo_output
    assert "test" in echo_output


###
# RaceTest evaluate_messages_test
###


class MessageCorruptionType(general_utils.PrettyEnum):
    """Message corruption types to test for"""

    SENDER_FAILED_TO_POST_SPAN = auto()
    RECEIVER_FAILED_TO_POST_SPAN = auto()
    HASH_CORRUPTED = auto()
    SIZE_CORRUPTED = auto()
    COUNT_FAILED = auto()
    NO_CORRUPTION = auto()


def create_spans_for_message(
    sender: str,
    receiver: str,
    trace_id: str,
    messageHash: str,
    message_corruption_type: MessageCorruptionType = MessageCorruptionType.NO_CORRUPTION,
) -> List[elasticsearch_utils.MessageSpan]:
    """
    Purpose:
        Create test spans for message and corrupt as necessary. Each message should have one sender
        span and one receiver span.
    Args:
        sender: Node to send from
        receiver: Node to send to
        trace_id: Trace ID of message
        messageHash: Hash of message
        message_corruption_type: Type of corruption to test for
    Return:
        spans: List of MessageSpans
    """
    spans = [
        elasticsearch_utils.MessageSpan(
            trace_id=trace_id,
            span_id=trace_id,
            start_time=0,
            source_persona=sender,
            messageSize="10",
            messageHash=messageHash,
            messageTestId="UT-TEST",
            messageFrom=sender,
            messageTo=receiver,
        ),
        elasticsearch_utils.MessageSpan(
            trace_id=trace_id,
            span_id=trace_id,
            start_time=0,
            source_persona=receiver,
            messageSize="10",
            messageHash=messageHash,
            messageTestId="UT-TEST",
            messageFrom=sender,
            messageTo=receiver,
        ),
    ]
    if message_corruption_type == MessageCorruptionType.SENDER_FAILED_TO_POST_SPAN:
        spans.pop(0)
    elif message_corruption_type == MessageCorruptionType.RECEIVER_FAILED_TO_POST_SPAN:
        spans.pop(1)
    elif message_corruption_type == MessageCorruptionType.HASH_CORRUPTED:
        spans[1]["messageHash"] = spans[1]["messageHash"] + "corruption"
    elif message_corruption_type == MessageCorruptionType.SIZE_CORRUPTED:
        spans[1]["messageHash"] = f'{int(spans[1]["messageSize"]) + 1}'
    return spans


def create_messages_for_client_pair(
    sender: str,
    receiver: str,
    msg_count: int,
    message_corruption_type: MessageCorruptionType = MessageCorruptionType.NO_CORRUPTION,
):
    """
    Purpose:
        Create test messages and corrupt as necessary.
    Args:
        sender: Node to send from
        receiver: Node to send to
        msg_count: Number of messages to send between nodes
        message_corruption_type: Type of corruption to test for
    Return:
        spans: List of MessageSpans
    """
    message_spans = []
    if message_corruption_type == MessageCorruptionType.COUNT_FAILED:
        msg_count -= 1
    for msg_num in range(1, msg_count + 1):
        message_spans.extend(
            create_spans_for_message(
                trace_id=f"{sender}->{receiver}_{msg_num}",
                messageHash=f"{sender}->{receiver}",
                sender=sender,
                receiver=receiver,
                message_corruption_type=message_corruption_type,
            )
        )
    return message_spans


def create_message_span_maps(
    recipient_sender_mapping: dict,
    msg_count: int,
    message_corruption_type: MessageCorruptionType = MessageCorruptionType.NO_CORRUPTION,
):
    """
    Purpose:
        Create organized message spans to mock elasticsearch_utils.get_message_spans
    Args:
        recipient_sender_mapping: Map of nodes pairs to send messages between
        msg_count: Number of messages to send between nodes
        message_corruption_type: Type of corruption to test for
    Return:
        spans: (source_persona_to_span, trace_id_to_span)
    """
    spans = []
    for receiver, senders in recipient_sender_mapping.items():
        for sender in senders:
            spans.extend(
                create_messages_for_client_pair(
                    sender=sender,
                    receiver=receiver,
                    msg_count=msg_count,
                    message_corruption_type=message_corruption_type,
                )
            )

    source_persona_to_span = {}
    trace_id_to_span = {}
    for span in spans:
        source_persona_to_span.setdefault(span["source_persona"], [])
        trace_id_to_span.setdefault(span["trace_id"], [])
        source_persona_to_span[span["source_persona"]].append(span)
        trace_id_to_span[span["trace_id"]].append(span)

    return (source_persona_to_span, trace_id_to_span)


@patch(
    "opensearchpy.OpenSearch",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.do_query",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.get_spans",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.create_query",
    MagicMock(),
)
@patch("time.time", Mock(side_effect=[0, 300]))
@patch("time.sleep", Mock())
@patch(
    "rib.utils.elasticsearch_utils.get_message_spans",
)
def test_evaluate_messages_test_default_success(
    mock_get_message_spans, mock_local_x2x_deployment
) -> int:
    """
    Purpose:
        Test evaluate_messages_test base case, all should pass
    Args:
        mock_get_message_spans: mock object to create testable spans
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    recipient_sender_mapping = {
        "race-client-00001": ["race-client-00002"],
        "race-client-00002": ["race-client-00001"],
    }

    mock_get_message_spans.return_value = create_message_span_maps(
        recipient_sender_mapping=recipient_sender_mapping, msg_count=1
    )

    test_id = "UT-TEST"
    test_result = testing_utils.TestResult("unit_test")

    myResult = testing_utils.evaluate_messages_test(
        elasticsearch_host_name=race_test.deployment.get_elasticsearch_hostname(),
        test_id=test_id,
        start_time=0,
        run_time=race_test.test_config.run_time,
        test_result=test_result,
        expected_message_count=1,
        recipient_sender_mapping=recipient_sender_mapping,
        evaluation_interval=race_test.test_config.evaluation_interval,
        range_name=race_test.deployment.get_range_name(),
    )
    race_test.test_results.append(myResult)

    assert len(race_test.test_results) == 1
    assert race_test.test_results[0].total == 2
    assert race_test.test_results[0].passed == 2
    assert race_test.test_results[0].failed == 0


@patch(
    "opensearchpy.OpenSearch",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.do_query",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.get_spans",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.create_query",
    MagicMock(),
)
@patch("time.time", Mock(side_effect=[0, 300]))
@patch("time.sleep", Mock())
@patch(
    "rib.utils.elasticsearch_utils.get_message_spans",
)
def test_evaluate_messages_test_multiple_messages_success(
    mock_get_message_spans, mock_local_x2x_deployment
) -> int:
    """
    Purpose:
        Test evaluate_messages_test with multiple messages between nodes, all should pass
    Args:
        mock_get_message_spans: mock object to create testable spans
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    recipient_sender_mapping = {
        "race-client-00001": ["race-client-00002"],
        "race-client-00002": ["race-client-00001"],
    }

    mock_get_message_spans.return_value = create_message_span_maps(
        recipient_sender_mapping=recipient_sender_mapping, msg_count=3
    )

    test_id = "UT-TEST"
    test_result = testing_utils.TestResult("unit_test")
    myResult = testing_utils.evaluate_messages_test(
        elasticsearch_host_name=race_test.deployment.get_elasticsearch_hostname(),
        test_id=test_id,
        start_time=0,
        run_time=race_test.test_config.run_time,
        test_result=test_result,
        expected_message_count=3,
        recipient_sender_mapping=recipient_sender_mapping,
        evaluation_interval=race_test.test_config.evaluation_interval,
        range_name=race_test.deployment.get_range_name(),
    )
    race_test.test_results.append(myResult)

    assert len(race_test.test_results) == 1
    assert race_test.test_results[0].total == 2
    assert race_test.test_results[0].passed == 2
    assert race_test.test_results[0].failed == 0


@patch(
    "opensearchpy.OpenSearch",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.do_query",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.get_spans",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.create_query",
    MagicMock(),
)
@patch("time.time", Mock(side_effect=[0, 300]))
@patch("time.sleep", Mock())
@patch(
    "rib.utils.elasticsearch_utils.get_message_spans",
)
def test_evaluate_messages_test_duplicate_messages_failure(
    mock_get_message_spans, mock_local_x2x_deployment
) -> int:
    """
    Purpose:
        Test evaluate_messages_test with duplicate messages between nodes, all should fail
    Args:
        mock_get_message_spans: mock object to create testable spans
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    recipient_sender_mapping = {
        "race-client-00001": ["race-client-00002"],
        "race-client-00002": ["race-client-00001"],
    }

    mock_get_message_spans.return_value = create_message_span_maps(
        recipient_sender_mapping=recipient_sender_mapping, msg_count=2
    )

    test_id = "UT-TEST"
    test_result = testing_utils.TestResult("unit_test")
    myResult = testing_utils.evaluate_messages_test(
        elasticsearch_host_name=race_test.deployment.get_elasticsearch_hostname(),
        test_id=test_id,
        start_time=0,
        run_time=race_test.test_config.run_time,
        test_result=test_result,
        expected_message_count=1,
        recipient_sender_mapping=recipient_sender_mapping,
        evaluation_interval=race_test.test_config.evaluation_interval,
        range_name=race_test.deployment.get_range_name(),
    )
    race_test.test_results.append(myResult)

    assert len(race_test.test_results) == 1
    assert race_test.test_results[0].total == 2
    assert race_test.test_results[0].passed == 0
    assert race_test.test_results[0].failed == 2

    # Expected Failure
    failed_expectations = f"expected 1, actual 2"

    # Regex
    error_matcher = re.compile(re.escape(failed_expectations))
    for dailed_expecatation in race_test.test_results[0].failed_expectations:
        error_matches = error_matcher.findall(dailed_expecatation)
        assert len(error_matches) == 1


@patch(
    "opensearchpy.OpenSearch",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.do_query",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.get_spans",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.create_query",
    MagicMock(),
)
@patch("time.time", Mock(side_effect=[0, 300]))
@patch("time.sleep", Mock())
@patch(
    "rib.utils.elasticsearch_utils.get_message_spans",
)
def test_evaluate_messages_test_recipient_missing(
    mock_get_message_spans, mock_local_x2x_deployment
) -> int:
    """
    Purpose:
        Test evaluate_messages_test when spans from the recipient are missing, all should fail
    Args:
        mock_get_message_spans: mock object to create testable spans
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    recipient_sender_mapping = {
        "race-client-00001": ["race-client-00002"],
        "race-client-00002": ["race-client-00001"],
    }

    mock_get_message_spans.return_value = create_message_span_maps(
        recipient_sender_mapping=recipient_sender_mapping,
        msg_count=1,
        message_corruption_type=MessageCorruptionType.RECEIVER_FAILED_TO_POST_SPAN,
    )

    test_id = "UT-TEST"
    test_result = testing_utils.TestResult("unit_test")
    myResult = testing_utils.evaluate_messages_test(
        elasticsearch_host_name=race_test.deployment.get_elasticsearch_hostname(),
        test_id=test_id,
        start_time=0,
        run_time=race_test.test_config.run_time,
        test_result=test_result,
        expected_message_count=1,
        recipient_sender_mapping=recipient_sender_mapping,
        evaluation_interval=race_test.test_config.evaluation_interval,
        range_name=race_test.deployment.get_range_name(),
    )
    race_test.test_results.append(myResult)

    assert len(race_test.test_results) == 1
    assert race_test.test_results[0].total == 2
    assert race_test.test_results[0].passed == 0
    assert race_test.test_results[0].failed == 2


@patch(
    "opensearchpy.OpenSearch",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.do_query",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.get_spans",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.create_query",
    MagicMock(),
)
@patch("time.time", Mock(side_effect=[0, 300]))
@patch("time.sleep", Mock())
@patch(
    "rib.utils.elasticsearch_utils.get_message_spans",
)
def test_evaluate_messages_test_sender_missing(
    mock_get_message_spans, mock_local_x2x_deployment
) -> int:
    """
    Purpose:
        Test evaluate_messages_test spans from the sender are missing, all should fail
    Args:
        mock_get_message_spans: mock object to create testable spans
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    recipient_sender_mapping = {
        "race-client-00001": ["race-client-00002"],
        "race-client-00002": ["race-client-00001"],
    }

    mock_get_message_spans.return_value = create_message_span_maps(
        recipient_sender_mapping=recipient_sender_mapping,
        msg_count=1,
        message_corruption_type=MessageCorruptionType.SENDER_FAILED_TO_POST_SPAN,
    )

    test_id = "UT-TEST"
    test_result = testing_utils.TestResult("unit_test")
    myResult = testing_utils.evaluate_messages_test(
        elasticsearch_host_name=race_test.deployment.get_elasticsearch_hostname(),
        test_id=test_id,
        start_time=0,
        run_time=race_test.test_config.run_time,
        test_result=test_result,
        expected_message_count=1,
        recipient_sender_mapping=recipient_sender_mapping,
        evaluation_interval=race_test.test_config.evaluation_interval,
        range_name=race_test.deployment.get_range_name(),
    )
    race_test.test_results.append(myResult)

    assert len(race_test.test_results) == 1
    assert race_test.test_results[0].total == 2
    assert race_test.test_results[0].passed == 0
    assert race_test.test_results[0].failed == 2


@patch(
    "opensearchpy.OpenSearch",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.do_query",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.get_spans",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.create_query",
    MagicMock(),
)
@patch("time.time", Mock(side_effect=[0, 300]))
@patch("time.sleep", Mock())
@patch(
    "rib.utils.elasticsearch_utils.get_message_spans",
)
def test_evaluate_messages_test_message_hash_corrupted(
    mock_get_message_spans, mock_local_x2x_deployment
) -> int:
    """
    Purpose:
        Test evaluate_messages_test message hash corrupted, all should fail
    Args:
        mock_get_message_spans: mock object to create testable spans
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    recipient_sender_mapping = {
        "race-client-00001": ["race-client-00002"],
        "race-client-00002": ["race-client-00001"],
    }

    mock_get_message_spans.return_value = create_message_span_maps(
        recipient_sender_mapping=recipient_sender_mapping,
        msg_count=1,
        message_corruption_type=MessageCorruptionType.HASH_CORRUPTED,
    )

    test_id = "UT-TEST"
    test_result = testing_utils.TestResult("unit_test")
    myResult = testing_utils.evaluate_messages_test(
        elasticsearch_host_name=race_test.deployment.get_elasticsearch_hostname(),
        test_id=test_id,
        start_time=0,
        run_time=race_test.test_config.run_time,
        test_result=test_result,
        expected_message_count=1,
        recipient_sender_mapping=recipient_sender_mapping,
        evaluation_interval=race_test.test_config.evaluation_interval,
        range_name=race_test.deployment.get_range_name(),
    )
    race_test.test_results.append(myResult)

    assert len(race_test.test_results) == 1
    assert race_test.test_results[0].total == 2
    assert race_test.test_results[0].passed == 0
    assert race_test.test_results[0].failed == 2


@patch(
    "opensearchpy.OpenSearch",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.do_query",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.get_spans",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.create_query",
    MagicMock(),
)
@patch("time.time", Mock(side_effect=[0, 300]))
@patch("time.sleep", Mock())
@patch(
    "rib.utils.elasticsearch_utils.get_message_spans",
)
def test_evaluate_messages_test_message_size_corrupted(
    mock_get_message_spans, mock_local_x2x_deployment
) -> int:
    """
    Purpose:
        Test evaluate_messages_test message size corrupted, all should fail
    Args:
        mock_get_message_spans: mock object to create testable spans
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    recipient_sender_mapping = {
        "race-client-00001": ["race-client-00002"],
        "race-client-00002": ["race-client-00001"],
    }

    mock_get_message_spans.return_value = create_message_span_maps(
        recipient_sender_mapping=recipient_sender_mapping,
        msg_count=1,
        message_corruption_type=MessageCorruptionType.SIZE_CORRUPTED,
    )

    test_id = "UT-TEST"
    test_result = testing_utils.TestResult("unit_test")
    myResult = testing_utils.evaluate_messages_test(
        elasticsearch_host_name=race_test.deployment.get_elasticsearch_hostname(),
        test_id=test_id,
        start_time=0,
        run_time=race_test.test_config.run_time,
        test_result=test_result,
        expected_message_count=1,
        recipient_sender_mapping=recipient_sender_mapping,
        evaluation_interval=race_test.test_config.evaluation_interval,
        range_name=race_test.deployment.get_range_name(),
    )
    race_test.test_results.append(myResult)

    assert len(race_test.test_results) == 1
    assert race_test.test_results[0].total == 2
    assert race_test.test_results[0].passed == 0
    assert race_test.test_results[0].failed == 2


@patch(
    "opensearchpy.OpenSearch",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.do_query",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.get_spans",
    MagicMock(),
)
@patch(
    "rib.utils.elasticsearch_utils.create_query",
    MagicMock(),
)
@patch("time.time", Mock(side_effect=[0, 300]))
@patch("time.sleep", Mock())
@patch(
    "rib.utils.elasticsearch_utils.get_message_spans",
)
def test_evaluate_messages_test_message_count_incorrect(
    mock_get_message_spans, mock_local_x2x_deployment
) -> int:
    """
    Purpose:
        Test evaluate_messages_test some message missing, all test cases should fail but some
        individual messages should be received
    Args:
        mock_get_message_spans: mock object to create testable spans
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    recipient_sender_mapping = {
        "race-client-00001": ["race-client-00002"],
        "race-client-00002": ["race-client-00001"],
    }

    mock_get_message_spans.return_value = create_message_span_maps(
        recipient_sender_mapping=recipient_sender_mapping,
        msg_count=2,
        message_corruption_type=MessageCorruptionType.COUNT_FAILED,
    )

    test_id = "UT-TEST"
    test_result = testing_utils.TestResult("unit_test")
    myResult = testing_utils.evaluate_messages_test(
        elasticsearch_host_name=race_test.deployment.get_elasticsearch_hostname(),
        test_id=test_id,
        start_time=0,
        run_time=race_test.test_config.run_time,
        test_result=test_result,
        expected_message_count=2,
        recipient_sender_mapping=recipient_sender_mapping,
        evaluation_interval=race_test.test_config.evaluation_interval,
        range_name=race_test.deployment.get_range_name(),
    )
    race_test.test_results.append(myResult)

    assert len(race_test.test_results) == 1
    assert race_test.test_results[0].total == 2
    assert race_test.test_results[0].passed == 0
    assert race_test.test_results[0].failed == 2
    assert race_test.test_results[0].failed_expectations

    # Expected Failure
    failed_expectations = f"expected 2, actual 1"

    # Regex
    error_matcher = re.compile(re.escape(failed_expectations))
    for dailed_expecatation in race_test.test_results[0].failed_expectations:
        error_matches = error_matcher.findall(dailed_expecatation)
        assert len(error_matches) == 1


###
# RaceTest evaluate_call_to_messages_test
###


@patch("rib.utils.testing_utils.evaluate_messages_test", Mock())
def test_evaluate_manual_messages_test_calls_evaluate_messages(
    mock_local_x2x_deployment,
) -> int:
    """
    Purpose:
        Test evaluate_manual_messages_test sets test_id
    Args:
        mock_evaluate_messages_test: mock evaluate_messages_test
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    race_test.evaluate_manual_messages_test(0)
    expected_test_it = "MM-TEST"

    assert testing_utils.evaluate_messages_test.call_count == 1
    assert expected_test_it == testing_utils.evaluate_messages_test.call_args_list[
        0
    ].kwargs.get("test_id")


@patch("rib.utils.testing_utils.evaluate_messages_test", Mock())
def test_evaluate_auto_messages_test_calls_evaluate_messages(
    mock_local_x2x_deployment,
) -> int:
    """
    Purpose:
        Test evaluate_auto_messages_test sets test_id
    Args:
        mock_evaluate_messages_test: mock evaluate_messages_test
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    race_test.evaluate_auto_messages_test(0)
    expected_test_it = "AM-TEST"

    assert testing_utils.evaluate_messages_test.call_count == 1
    assert expected_test_it == testing_utils.evaluate_messages_test.call_args_list[
        0
    ].kwargs.get("test_id")


@patch("rib.utils.testing_utils.evaluate_messages_test", Mock())
def test_evaluate_bootstrap_messages_test_calls_evaluate_messages(
    mock_local_x2x_deployment,
) -> int:
    """
    Purpose:
        Test evaluate_manual_messages_test sets test_id
    Args:
        mock_evaluate_messages_test: mock evaluate_messages_test
        mock_local_x2x_deployment: a mock 2x2 deployment
    """
    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    race_test.evaluate_bootstrap_test(0)
    expected_test_it = "BS-TEST"

    assert testing_utils.evaluate_messages_test.call_count == 1
    assert expected_test_it == testing_utils.evaluate_messages_test.call_args_list[
        0
    ].kwargs.get("test_id")


###
# RaceTest execute_manual_messages_test
###


def test_RaceTest_execute_manual_messages_test(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest validate properly executes the manual message test
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    race_test.execute_manual_messages_test()

    sent_message_calls = []
    for call_args in mock_local_x2x_deployment.send_message.call_args_list:
        sent_message_calls.append(call_args[1]["message_content"])

    assert mock_local_x2x_deployment.send_message.call_count == 2
    assert "race-client-00001->race-client-00002 (1/1)" in sent_message_calls
    assert "race-client-00002->race-client-00001 (1/1)" in sent_message_calls


###
# RaceTest execute_auto_messages_test
###


def test_RaceTest_execute_auto_messages_test(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest validate properly executes the auto message test
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    race_test.execute_auto_messages_test()

    sent_message_calls = []
    for call_args in mock_local_x2x_deployment.send_message.call_args_list:
        sent_message_calls.append(
            f"{call_args[1]['sender']}->{call_args[1]['recipient']}"
        )

    assert mock_local_x2x_deployment.send_message.call_count == 2
    assert "race-client-00001->race-client-00002" in sent_message_calls
    assert "race-client-00002->race-client-00001" in sent_message_calls


@patch(
    "click.echo", MagicMock()
)  # Suppress log output, the mock isn't actually used for testing.
def test_RaceTest_run_setup_steps(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest runs setup steps properly
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    with mock.patch("time.sleep") as sleep_mock:
        race_test.run_setup_steps()

        assert sleep_mock.call_count == 2
        assert sleep_mock.call_args_list[0].args[0] == 0
        assert sleep_mock.call_args_list[1].args[0] == 30
        assert mock_local_x2x_deployment.rotate_logs.call_count == 1
        assert mock_local_x2x_deployment.start.call_count == 1


@patch(
    "click.echo", MagicMock()
)  # Suppress log output, the mock isn't actually used for testing.
def test_RaceTest_run_test_steps(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest runs test steps properly
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    with mock.patch("time.sleep") as sleep_mock:
        race_test.run_test_steps()

        assert sleep_mock.call_count == 1
        assert sleep_mock.call_args_list[0].args[0] == 30


@patch(
    "click.echo", MagicMock()
)  # Suppress log output, the mock isn't actually used for testing.
@patch("rib.utils.testing_utils.RaceTest.run_test_steps", MagicMock())
@patch("rib.utils.testing_utils.RaceTest.run_evaluation_steps", MagicMock())
def test_RaceTest_run_deployment_test(mock_local_x2x_deployment) -> int:
    """
    Purpose:
        Test RaceTest runs deployment test properly

        run_test_steps and run_evaluation_steps have separate specific unit tests
    Args:
        mock_local_x2x_deployment: a mock 2x2 deployment
    """

    race_test = testing_utils.RaceTest(deployment=mock_local_x2x_deployment)

    with mock.patch("time.sleep") as sleep_mock:
        race_test.run_deployment_test()

        # Rotate logs should be called twice: once during setup and once again during teardown.
        assert mock_local_x2x_deployment.rotate_logs.call_count == 2
        assert mock_local_x2x_deployment.pull_runtime_configs.call_count == 1
