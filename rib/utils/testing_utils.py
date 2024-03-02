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
        Testing Utilities for aiding test RACE and deployments
"""

# Python Library Imports
from copy import deepcopy
import warnings
from opensearchpy import OpenSearch as Elasticsearch
from opensearchpy.exceptions import OpenSearchWarning as ElasticsearchWarning
import click
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional
from rib.deployment.rib_aws_deployment import RibAwsDeployment

# Local Python Library Imports
from rib.deployment.rib_deployment import RibDeployment
from rib.deployment.status.rib_deployment_status import Require
from rib.utils import error_utils, general_utils, elasticsearch_utils, status_utils


###
# Globals
###


logger = logging.getLogger(__name__)


###
# Custom Dataclasses
###


@dataclass
class TestConfig:
    """Config for a test plan"""

    run_time: int = 240
    start_timeout: int = 300
    delay_start: int = 15
    delay_execute: int = 15
    delay_evaluation: int = 30
    evaluation_interval: int = 15
    is_running: bool = False
    network_manager_bypass: bool = False
    comms_channel: Optional[str] = None
    comms_channel_type: Optional[str] = None
    no_down: bool = False


@dataclass
class TestCase:
    """Test Case for a test"""

    name: str
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """A Single RACE Test Result"""

    test_case: str
    total: int = 0
    passed: int = 0
    failed: int = 0
    failed_expectations: List[str] = field(default_factory=list)


###
# RaceTest Class
###


class RaceTest:
    """
    Purpose:
        Class for wrapping tests of the RACE system using deployments
        and RiB
    """

    clients: List[str] = None
    servers: List[str] = None
    recipient_sender_mapping: Dict[str, List[str]] = None
    bootstrap_mapping: List[Dict[str, str]] = None
    bootstrap_verification_mapping: Dict[str, List[str]] = None
    test_cases: List[TestCase] = None
    test_config: TestConfig = None
    test_results: List[TestResult] = None
    deployment: RibDeployment = None

    test_case_function_mapping: Dict[str, Dict[str, Callable]] = {}

    ###
    # Lifecycle Methods
    ###

    def __init__(
        self,
        deployment: RibDeployment,
        run_time: int = 30,
        start_timeout: int = 300,
        delay_start: int = 0,
        delay_execute: int = 30,
        delay_evaluation: int = 30,
        evaluation_interval: int = 15,
        is_running: bool = False,
        test_plan_file: Optional[str] = None,
        test_plan_json: Optional[str] = None,
        comms_channel: Optional[str] = None,
        comms_channel_type: Optional[str] = None,
        network_manager_bypass: bool = False,
        no_down: bool = False,
    ) -> None:
        """
        Purpose:
            Initialize the Test Plan Object which will be used to test a RACE deployment/
            channel
        Args:
            deployment: The deployment to use for the test
            run_time: The runtime (seconds) of the test. will doa  sleep to allow test to run
            start_timeout: Time to wait for deployment to start
            delay_start: Delay between upping the deployment and starting the deployment;
                used for letting whiteboards really get started
            delay_execute: Delay between starting the deployment and running steps;
                used for letting the deployment stabalize
            delay_evaluation: Delay between starting test execution and running evaluation steps;
                used to reduce wasteful queries to elasticsearch
            evaluation_interval: The amount of time (seconds) between attempts to evaluate tests
            is_running: if we should use a running deployment
            test_plan_file: Test Plan file to load and use
            test_plan_json: Test Plan JSON passed in argument to use
            comms_channel: Comms channel being tested, will use network-manager-bypass to test this
                channel only
            comms_channel_type: If the channel is C2S or S2S, changes test
            network_manager_bypass: If network-manager-bypass is enabled
            no_down: Prevent downing the deployment once the run is complete to allow debugging
        Returns:
            N/A
        Raises:
            error_utils.RIB600: if validation fails
        """

        self.test_case_function_mapping = {
            "manual_messages": {
                "execute": self.execute_manual_messages_test,
                "evaluate": self.evaluate_manual_messages_test,
            },
            "auto_messages": {
                "execute": self.execute_auto_messages_test,
                "evaluate": self.evaluate_auto_messages_test,
            },
            "bootstrap": {
                "execute": self.execute_bootstrap_test,
                "evaluate": self.evaluate_bootstrap_test,
            },
        }

        # Set the Deployment (needed to get defaults/clients/mappings/etc)
        self.deployment = deployment

        # Set the test config from the CLI args, This will be the default TestConfig
        # and will inform the default
        self.test_config = TestConfig(
            run_time=run_time,
            start_timeout=start_timeout,
            delay_start=delay_start,
            delay_execute=delay_execute,
            delay_evaluation=delay_evaluation,
            evaluation_interval=evaluation_interval,
            is_running=is_running,
            comms_channel=comms_channel,
            comms_channel_type=comms_channel_type,
            network_manager_bypass=network_manager_bypass,
            no_down=no_down,
        )

        # Load default values
        self.load_default_tests_and_mapping()

        # If file/json are set, then we will load data from them (file first then json)
        # Priority: JSON -> File -> CLI -> Defaults
        if test_plan_file is not None:
            self.load_from_file(test_plan_file)

        if test_plan_json is not None:
            self.load_from_json(test_plan_json)

        # Validate the test plan before returning, throw exception if not valid
        self.validate()

    def __repr__(self) -> str:
        """
        Purpose:
            Representation of the RaceTest object.
        Args:
            N/A
        Returns:
            RaceTest: most critical properties
        """

        return (
            f"<RACE Test, "
            f"clients = {self.clients}"
            f", servers = {self.servers}"
            f", recipient_sender_mapping = {self.recipient_sender_mapping}"
            f", test_cases = {self.test_cases}"
            f", test_config = {self.test_config}"
            f", test_results = {self.test_results}"
            f", deployment = {self.deployment}"
            f">"
        )

    ###
    # Properties
    ###

    @property
    def failed(self) -> bool:
        """If the test failed"""
        return any(x.failed for x in self.test_results)

    @property
    def passed(self) -> bool:
        """If the test passed"""
        return all(x.passed for x in self.test_results)

    @property
    def total_failed(self) -> int:
        """Total number of tests that failed"""
        return sum([x.failed for x in self.test_results])

    @property
    def total_passed(self) -> int:
        """Total number of tests that passed"""
        return sum([x.passed for x in self.test_results])

    @property
    def has_bootstrap_test_case(self) -> bool:
        """Whether any bootstrap test cases will be executed"""
        return any(
            [
                x.name == "bootstrap" and x.settings.get("enabled", False)
                for x in self.test_cases
            ]
        )

    ###
    # Load Methods
    ###

    def load_from_file(self, test_plan_file: str) -> None:
        """
        Purpose:
            Load RaceTest values from test plan file
        Args:
            test_plan_file: Test Plan file to load and use
        Returns:
            N/A
        Raises:
            Exception: if loading the file fails
        """

        loaded_test_plan = general_utils.load_file_into_memory(
            test_plan_file, data_format="json"
        )
        self.handle_loaded_test_plan(loaded_test_plan)

    def load_from_json(self, test_plan_json: str) -> None:
        """
        Purpose:
            Load RaceTest values from test plan json/dict
        Args:
            test_plan_json: Test Plan Escaped JSON passed in argument to use
        Returns:
            N/A
        Raises:
            Exception: if the test_plan data is invalid
        """

        loaded_test_plan = json.loads(test_plan_json)
        self.handle_loaded_test_plan(loaded_test_plan)

    def handle_loaded_test_plan(self, loaded_test_plan: Dict[str, Any]) -> None:
        """
        Purpose:
            Handle a loaded test plan. functionality is the same for JSON + File, so
            this will be called by both
        Args:
            loaded_test_plan: The loaded test plan
        Returns:
            N/A
        Raises:
            Exception: if the test_plan data is invalid
        """

        # Return quick if test plan has no data
        if not loaded_test_plan:
            return

        # Set Clients/Server/Mapping if it is set
        if loaded_test_plan.get("clients", None):
            self.clients = loaded_test_plan.get("clients", [])
        if loaded_test_plan.get("servers", None):
            self.servers = loaded_test_plan.get("servers", [])
        if loaded_test_plan.get("recipient_sender_mapping", None):
            self.recipient_sender_mapping = loaded_test_plan.get(
                "recipient_sender_mapping", {}
            )
        if loaded_test_plan.get("bootstrap_mapping", None):
            self.bootstrap_mapping = loaded_test_plan.get("bootstrap_mapping", {})
        if loaded_test_plan.get("bootstrap_verification_mapping", None):
            self.bootstrap_verification_mapping = loaded_test_plan.get(
                "bootstrap_verification_mapping", {}
            )

        # If this test plan sets clients/servers/both but NOT the sender/recipient
        # mapping, generate the sender/recipient mapping
        if not loaded_test_plan.get("recipient_sender_mapping", None) and (
            loaded_test_plan.get("clients", None)
            or loaded_test_plan.get("servers", None)
        ):
            self.generate_recipient_sender_mapping()

        # If this test plan sets clients/servers/both but NOT the sender/recipient
        # mapping, generate the bootstrap mapping
        if not loaded_test_plan.get("bootstrap_mapping", None) and (
            loaded_test_plan.get("clients", None)
            or loaded_test_plan.get("servers", None)
        ):
            self.generate_bootstrap_mapping()

        if not loaded_test_plan.get("bootstrap_verification_mapping", None) and (
            loaded_test_plan.get("clients", None)
            or loaded_test_plan.get("servers", None)
        ):
            self.generate_bootstrap_verification_mapping

        # If there are test cases, create the TestCase objects and set the values
        if loaded_test_plan.get("test_cases", None):
            self.test_cases = []
            for test_case in loaded_test_plan.get("test_cases", []):
                self.test_cases.append(
                    TestCase(
                        name=test_case["name"],
                        settings=test_case["settings"],
                    )
                )

        # If there is a test_config, create the TestConfig object and set the values
        if loaded_test_plan.get("test_config", None):
            self.test_config = TestConfig(**loaded_test_plan.get("test_config", {}))

    def load_default_tests_and_mapping(self) -> None:
        """
        Purpose:
            Set the default test cases, and mappings based on the deployment and configs
        Args:
            N/A
        Returns:
            N/A
        Raises:
            N/A
        """

        # Clients/Servers
        self.clients = []
        self.servers = []
        self.recipient_sender_mapping = {}

        # Test Cases (Default)
        self.test_cases = [
            TestCase(
                name="bootstrap",
                settings={"enabled": True, "test_id": "BS-TEST"},
            ),
            TestCase(
                name="manual_messages",
                settings={"enabled": True, "quantity": 1, "test_id": "MM-TEST"},
            ),
            TestCase(
                name="auto_messages",
                settings={
                    "enabled": True,
                    "period": 10,
                    "quantity": 5,
                    "size": 140,
                    "test_id": "AM-TEST",
                },
            ),
        ]

        # Set Empty Result
        self.test_results = []

        # Set clients and servers if they are not set
        if not self.clients:
            self.clients = deepcopy(self.deployment.client_personas)
        if not self.servers:
            self.servers = deepcopy(self.deployment.server_personas)

        # Set Sender/Recipient Mapping if it is not set
        if not self.recipient_sender_mapping:
            self.generate_recipient_sender_mapping()

        # Set Bootstrap Mapping if it is not set
        if not self.bootstrap_mapping:
            self.generate_bootstrap_mapping()

        # Set Bootstrap Verification Mapping if it is not set
        if not self.bootstrap_verification_mapping:
            self.generate_bootstrap_verification_mapping()

    ###
    # Export Methods
    ###

    def export_plan_to_dict(self) -> Dict[str, Any]:
        """
        Purpose:
            export the test plan to reuse in a new test later.
            Will return a dict of the data that would be in a test plan file
        Args:
            N/A
        Returns:
            exported_plan: a dict of the test plan to load to a file
                or inspect
        Raises:
            N/A
        """

        return {
            "clients": self.clients,
            "servers": self.servers,
            "recipient_sender_mapping": self.recipient_sender_mapping,
            "bootstrap_mapping": self.bootstrap_mapping,
            "bootstrap_verification_mapping": self.bootstrap_verification_mapping,
            "test_config": asdict(self.test_config),
            "test_cases": [asdict(test_case) for test_case in self.test_cases],
        }

    def export_plan_to_str(self) -> str:
        """
        Purpose:
            export the test plan to reuse in a new test later.
            Will escape the data in the test plan file
        Args:
            N/A
        Returns:
            escaped_plan: escaped plan that can be passed in through the CLI to
                run a test with `rib deployment <mode> test`
        Raises:
            N/A
        """

        return json.dumps(json.dumps(self.export_plan_to_dict()))

    def export_plan_to_file(self, export_file: str, overwrite: bool) -> None:
        """
        Purpose:
            export the test plan to reuse in a new test later.
            Will take the dict from a test plan and dump it to a specified file
        Args:
            export_file: file to write the test plan to
            overwrite: if we will overwrite the file
        Returns:
            N/A
        Raises:
            N/A
        """

        general_utils.write_data_to_file(
            export_file,
            self.export_plan_to_dict(),
            data_format="json",
            overwrite=overwrite,
        )

    ###
    # Generate Sender Recipient Mapping
    ###

    def generate_recipient_sender_mapping(self) -> None:
        """
        Purpose:
            Generate a sender/recipient mapping depending on the deployment, clients,
            servers, whether network-manager-bypass is enabled, and the tested channel
        Args:
            N/A
        Returns:
            N/A
        Raises:
            N/A
        """

        self.recipient_sender_mapping = {}

        if self.test_config.network_manager_bypass:
            # Client <-> Server
            if self.test_config.comms_channel_type in ("c2s", "all"):
                # Client -> Server
                for sender in self.clients:
                    for recipient in self.servers:
                        self.recipient_sender_mapping.setdefault(recipient, [])
                        self.recipient_sender_mapping[recipient].append(sender)

                # Server -> Client
                for sender in self.servers:
                    for recipient in self.clients:
                        self.recipient_sender_mapping.setdefault(recipient, [])
                        self.recipient_sender_mapping[recipient].append(sender)

            # Server -> Server
            elif self.test_config.comms_channel_type in ("s2s", "all"):
                for sender in self.servers:
                    for recipient in self.servers:
                        if sender == recipient:
                            continue
                        self.recipient_sender_mapping.setdefault(recipient, [])
                        self.recipient_sender_mapping[recipient].append(sender)

            else:
                raise Exception(
                    f"Cannot have network-manager-bypass but not comms channel and type"
                )

        else:
            # Client <-> Client
            for sender in self.clients:
                for recipient in self.clients:
                    if sender == recipient:
                        continue
                    self.recipient_sender_mapping.setdefault(recipient, [])
                    self.recipient_sender_mapping[recipient].append(sender)

    ###
    # Generate Bootstrap Mapping
    ###

    def generate_bootstrap_mapping(self) -> None:
        """
        Purpose:
            Generate a bootstrap mapping depending on the deployment clients

            Will set self.bootstrap_mapping, which is a dict of a target node to be
            bootstrapped and the value being the introducer node that will do the bootstrapping
        Args:
            N/A
        Returns:
            N/A
        Raises:
            N/A
        """

        self.bootstrap_mapping = []

        if not self.deployment.bootstrap_client_personas:
            return

        if not self.deployment.genesis_client_personas:
            raise Exception(
                f"No Genesis Clients to Bootstrap new Clients in {self.deployment.name}"
            )

        # Logic to build the introducers
        # TODO (longer term), once 2.1.0 is out, we should be able to have bootstrapped
        # nodes introduce other bootstrapped nodes once they are in the network
        # e.g. c1 introduces c2 who then introduces c3. This would make the test
        # take more time, but is also a really valuable test
        possible_introducers = self.deployment.genesis_client_personas

        # Setting the possible targets to bootstrap
        possible_targets = self.deployment.bootstrap_client_personas

        genesis_idx = 0
        genesis_length = len(possible_introducers)
        for genesis_idx, bootstrap_client in enumerate(possible_targets):
            self.bootstrap_mapping.append(
                {
                    "introducer": possible_introducers[genesis_idx % genesis_length],
                    "target": bootstrap_client,
                    "architecture": "auto",
                }
            )

    def generate_bootstrap_verification_mapping(self) -> None:
        """
        Purpose:
            Generate a bootstrap verification mapping depending on the deployment clients

            Will set self.bootstrap_verification_mapping, which is a dict of a bootstrapped node and
            a genesis node (other that the introducer when possible) to send a verification message
        Args:
            N/A
        Returns:
            N/A
        Raises:
            N/A
        """

        self.bootstrap_verification_mapping = {}
        verifiers_length = len(self.deployment.genesis_client_personas) - 1
        bootstrap_pair_index = 0
        for bootstrap in self.bootstrap_mapping:
            bootstrap_target = bootstrap["target"]
            bootstrap_introducer = bootstrap["introducer"]
            bootstrap_pair_index += 1
            if len(self.deployment.genesis_client_personas) > 1:
                # Use a node other than the introducer if possible
                verifier_node = list(
                    set(self.deployment.genesis_client_personas)
                    - set([bootstrap_introducer])
                )[bootstrap_pair_index % verifiers_length]
            else:
                verifier_node = bootstrap_introducer

            self.bootstrap_verification_mapping.setdefault(bootstrap_target, [])
            self.bootstrap_verification_mapping[bootstrap_target].append(verifier_node)
            self.bootstrap_verification_mapping.setdefault(verifier_node, [])
            self.bootstrap_verification_mapping[verifier_node].append(bootstrap_target)

    ###
    # Validation of the Test Plan
    ###

    def validate(self) -> None:
        """
        Purpose:
            Validate that a test plan has clients, servers, a mapping, and configs
        Args:
            N/A
        Returns:
            N/A
        Raises:
            error_utils.RIB600: if validation fails
        """

        try:
            for test_case in self.test_cases:
                if test_case.name not in self.test_case_function_mapping:
                    raise error_utils.RIB600(
                        f"Test Case {test_case.name} Not a valid test case"
                    )

            assert self.test_config.run_time is not None, "Test Plans need Run Time"
            assert (
                self.test_config.delay_execute is not None
            ), "Test Plans need Delay Execute"
            assert (
                self.test_config.delay_start is not None
            ), "Test Plans need Delay Start"

            missing_clients = []
            for client in self.clients:
                if client not in self.deployment.client_personas:
                    missing_clients.append(client)
            if missing_clients:
                raise error_utils.RIB600(
                    f"Clients ({', '.join(missing_clients)} do not exist in the deployment"
                )

            missing_servers = []
            for server in self.servers:
                if server not in self.deployment.server_personas:
                    missing_servers.append(server)
            if missing_servers:
                raise error_utils.RIB600(
                    f"Servers ({', '.join(missing_servers)} do not exist in the deployment"
                )
        except Exception as err:
            click.echo(f"Test Plan Failed Validation: {self}")
            raise err

    ###
    # Test Executor
    ###

    def run_deployment_test(self, cli_context: click.core.Context = None) -> None:
        """
        Purpose:
            Run a test against a deployment from end to end
            (up->start->test->stop->down->eval)
        Args:
            cli_context: cli context used to get token information if needed
        Returns:
            N/A
        Raises:
            TODO
        """

        # Run Setup for test (or use deployment already running)
        if not self.test_config.is_running:
            self.run_setup_steps(cli_context)
        else:
            self.verify_deployment_is_running()

        error = None
        try:
            start_time = time.time() * 1000
            # Run Test Steps as Defined in the test plan
            self.run_test_steps()

            # Evaluate Test Steps
            # TODO, split this up to runtime evaluation and post-run evalutation
            # for tests that look at things that occur when shutting down
            self.run_evaluation_steps(start_time)

        except KeyboardInterrupt as err:
            # Catching keyboard signals (ctrl+c) to teardown deployment before exiting
            click.echo("Test cancelled by user")
            error = err
        except Exception as err:
            click.echo(f"Error occurred while running tests: {err}")
            error = err
        finally:
            click.echo(
                "Stopping test. "
                f"{'Tearing down deployment' if not self.test_config.is_running and not self.test_config.no_down else ''}"
            )
            # Run Teardown for test (ignore if deployment was running before the test)
            if not self.test_config.is_running and not self.test_config.no_down:
                self.run_teardown_steps()

        if error is not None:
            raise error

    ###
    # Run Test Functions
    ###

    def run_setup_steps(self, cli_context: click.core.Context = None) -> None:
        """
        Purpose:
            Run steps required for starting up the application. Remove old logs, start the
            app, etc
        Args:
            cli_context: cli context used to get token information if needed
        Returns:
            N/A
        """
        click.echo("Running Setup Steps")

        click.echo("Standing Up Deployment")
        # Timeout 10 mins to make sure android has time to start. this is longer than
        # the default 5 mins as in a normal case the user can check the status anc
        # continue the deployment
        if isinstance(self.deployment, RibAwsDeployment):
            self.deployment.up(
                last_up_command="upped from automated test deployment",
                force=False,
                timeout=3_600,
            )
        else:
            self.deployment.up(
                last_up_command="upped from automated test deployment",
                force=False,
                timeout=600,
            )

        click.echo(
            f"Waiting {self.test_config.delay_start} seconds before starting nodes"
            " to allow for external services and race nodes containers to properly start"
        )
        time.sleep(self.test_config.delay_start)

        click.echo("Deleting Logs")
        self.deployment.rotate_logs(
            backup_id="",
            delete=True,
            force=False,
            nodes=None,
            timeout=120,
        )

        click.echo("Starting Deployment")
        self.deployment.start(timeout=self.test_config.start_timeout)

        click.echo(
            f"Waiting {self.test_config.delay_execute} seconds before executing tests"
            " to allow for nodes to initialize and network to stabilize"
        )
        time.sleep(self.test_config.delay_execute)

    def verify_deployment_is_running(self) -> None:
        """
        Purpose:
            Verifies that all nodes of the deployment are in the correct state (up/started) before
            executing any tests.
        Args:
            N/A
        Returns:
            N/A
        """

        self.deployment.status.verify_deployment_is_active("test")
        # All genesis nodes have to have been started
        self.deployment.status.get_nodes_that_match_status(
            action="test",
            personas=self.deployment.genesis_personas,
            race_status=[status_utils.RaceStatus.RUNNING],
            require=Require.ALL,
        )
        # If performing a bootstrap test, non-genesis nodes need to be a ready-to-be-bootstrapped
        # state, otherwise they need to be running
        if self.deployment.bootstrap_client_personas:
            self.deployment.status.get_nodes_that_match_status(
                action="test",
                personas=self.deployment.bootstrap_client_personas,
                app_status=[
                    status_utils.AppStatus.NOT_INSTALLED
                    if self.has_bootstrap_test_case
                    else status_utils.AppStatus.RUNNING
                ],
                race_status=[
                    status_utils.RaceStatus.NOT_REPORTING
                    if self.has_bootstrap_test_case
                    else status_utils.RaceStatus.RUNNING
                ],
                require=Require.ALL,
            )

    def run_test_steps(self) -> None:
        """
        Purpose:
            Run steps for testing the application
        Args:
            N/A
        Returns:
            N/A
        """

        click.echo("Running Test Steps")

        for test_case in self.test_cases:
            click.echo(f"Running Test Steps: {test_case.name}")
            if not test_case.settings.get("enabled", False):
                continue
            self.test_case_function_mapping[test_case.name]["execute"]()

        click.echo(
            f"Sleeping for {self.test_config.delay_evaluation} seconds (Test takes time to run)"
        )
        time.sleep(self.test_config.delay_evaluation)

    def run_evaluation_steps(self, start_time: int) -> None:
        """
        Purpose:
            Run steps for evaluating the application
        Args:
            start_time: Time the test was kicked off
        Returns:
            N/A
        """
        click.echo("Running Evaluation Steps")
        for test_case in self.test_cases:
            click.echo(f"Running Eval Steps: {test_case.name}")
            if not test_case.settings.get("enabled", False):
                continue
            self.test_case_function_mapping[test_case.name]["evaluate"](start_time)

    def run_teardown_steps(self) -> None:
        """
        Purpose:
            Run steps required for tearing down the application.
        Args:
            N/A
        Returns:
            Exception: If stopping the deployment fails. Capture and try to down
                even if there is a exception
        """
        click.echo("Test Teardown: Running Teardown Steps")

        try:
            click.echo("Test Teardown: Stopping Deployment")
            self.deployment.stop()
            click.echo("Test Teardown: Deployment has been stopped")
        except Exception as err:
            click.echo(f"Test Teardown: ERROR: failed to stop deployment: {err}")
            raise err
        finally:
            if self.deployment.rib_mode == "local":
                try:
                    click.echo("Test Teardown: Backing Up Logs...")
                    self.deployment.rotate_logs(
                        backup_id="test-deployment-logs",
                        delete=False,
                        force=True,
                        nodes=None,
                        timeout=600,
                    )
                    click.echo("Test Teardown: Backed Up Logs")
                except Exception as err:
                    click.echo(f"Test Teardown: ERROR: failed to backup logs: {err}")

                try:
                    click.echo("Test Teardown: Backing Up Configs...")
                    self.deployment.pull_runtime_configs(
                        config_name="test-deployment-configs",
                        overwrite=True,
                        timeout=600,
                    )
                    click.echo("Test Teardown: Backed Up Configs")
                except Exception as err:
                    click.echo(f"Test Teardown: ERROR: failed to backup configs: {err}")

            click.echo("Test Teardown: Downing Deployment")
            self.deployment.down(
                last_down_command="downed from automated test", force=True
            )
            click.echo("Test Teardown: Deployment has been downed")

    ###
    # Execute Test Functions
    ###

    def execute_manual_messages_test(self) -> None:
        """
        Purpose:
            Run the "Manual Messages" Test, Will send a manual message from each node to
            each node based on the test plan
        Args:
            N/A
        Returns:
            N/A
        """

        test_case = next(x for x in self.test_cases if x.name == "manual_messages")
        test_id = test_case.settings["test_id"]
        total_msgs = test_case.settings["quantity"]
        for recipient, senders in self.recipient_sender_mapping.items():
            for sender in senders:
                for msg_idx in range(1, total_msgs + 1):
                    self.deployment.send_message(
                        "manual",
                        message_content=f"{sender}->{recipient} ({msg_idx}/{total_msgs})",
                        recipient=recipient,
                        sender=sender,
                        network_manager_bypass_route=self.test_config.comms_channel,
                        test_id=test_id,
                    )

    def execute_auto_messages_test(self) -> None:
        """
        Purpose:
            Run the "Auto Messages" Test, Will send a auto messages from each node to
            each node based on the test plan
        Args:
            N/A
        Returns:
            N/A
        """

        test_case = next(x for x in self.test_cases if x.name == "auto_messages")
        test_id = test_case.settings["test_id"]

        for recipient, senders in self.recipient_sender_mapping.items():
            for sender in senders:
                self.deployment.send_message(
                    "auto",
                    message_period=test_case.settings["period"],
                    message_quantity=test_case.settings["quantity"],
                    message_size=test_case.settings["size"],
                    recipient=recipient,
                    sender=sender,
                    network_manager_bypass_route=self.test_config.comms_channel,
                    test_id=test_id,
                )

    def execute_bootstrap_test(self) -> None:
        """
        Purpose:
            Run the "Bootstrap" Test. This test will run through the bootstrap_mapping
            (as defined in the test plan or generated) and
        Args:
            N/A
        Returns:
            N/A
        """

        test_case = next(x for x in self.test_cases if x.name == "bootstrap")
        test_id = test_case.settings["test_id"]

        if not self.deployment.bootstrap_client_personas:
            # raise Exception(f"No Bootstrap clients in {self.deployment.name} to test")
            print(
                f"WARNING: No Bootstrap clients in {self.deployment.config['name']} to test"
            )

        for bootstrap in self.bootstrap_mapping:
            bootstrap_target = bootstrap["target"]
            bootstrap_introducer = bootstrap["introducer"]
            bootstrap_architecture = bootstrap["architecture"]
            print(
                f"Bootstrapping {bootstrap_target} using {bootstrap_introducer} as introducer"
            )
            self.deployment.bootstrap_node(
                force=False,
                introducer=bootstrap_introducer,
                target=bootstrap_target,
                passphrase=bootstrap_target,  # Set the passphrase as the target, which is unique
                architecture=bootstrap_architecture,
                bootstrapChannelId="",
                timeout=600,
            )
        for recipient, senders in self.bootstrap_verification_mapping.items():
            for sender in senders:
                self.deployment.send_message(
                    "manual",
                    message_content=f"{sender}->{recipient} bootstrap test",
                    recipient=recipient,
                    sender=sender,
                    test_id=test_id,
                )

    ###
    # Evaluate Test Functions
    ###

    def evaluate_manual_messages_test(self, start_time: int) -> None:
        """
        Purpose:
            Evaluate the "Manual Messages" Test and return results
        Args:
            start_time: Time the test was kicked off
        Returns:
            N/A
        """

        test_result = TestResult(test_case="manual_messages")
        test_case = next(x for x in self.test_cases if x.name == "manual_messages")
        expected_message_count = test_case.settings["quantity"]
        test_id = test_case.settings["test_id"]

        myResult = evaluate_messages_test(
            elasticsearch_host_name=self.deployment.get_elasticsearch_hostname(),
            test_id=test_id,
            start_time=start_time,
            run_time=self.test_config.run_time,
            test_result=test_result,
            expected_message_count=expected_message_count,
            recipient_sender_mapping=self.recipient_sender_mapping,
            evaluation_interval=self.test_config.evaluation_interval,
            range_name=self.deployment.get_range_name(),
        )
        # append the test result here
        self.test_results.append(myResult)

    def evaluate_auto_messages_test(self, start_time: int) -> None:
        """
        Purpose:
            Evaluate the "Auto Messages" Test and return results
        Args:
            start_time: Time the test was kicked off
        Returns:
            N/A
        """

        test_result = TestResult(test_case="auto_messages")
        test_case = next(x for x in self.test_cases if x.name == "auto_messages")
        expected_message_count = test_case.settings["quantity"]
        expected_message_size = test_case.settings["size"]
        test_id = test_case.settings["test_id"]

        myResult = evaluate_messages_test(
            elasticsearch_host_name=self.deployment.get_elasticsearch_hostname(),
            test_id=test_id,
            start_time=start_time,
            run_time=self.test_config.run_time,
            test_result=test_result,
            expected_message_count=expected_message_count,
            recipient_sender_mapping=self.recipient_sender_mapping,
            expected_message_size=expected_message_size,
            evaluation_interval=self.test_config.evaluation_interval,
            range_name=self.deployment.get_range_name(),
        )
        # append the test result here
        self.test_results.append(myResult)

    def evaluate_bootstrap_test(self, start_time: int) -> None:
        """
        Purpose:
            Evaluate the "Bootstrap" Test and return results
        Args:
            start_time: Time the test was kicked off
        Returns:
            N/A
        """

        test_result = TestResult(test_case="bootstrap")
        test_case = next(x for x in self.test_cases if x.name == "bootstrap")
        test_id = test_case.settings["test_id"]

        myResult = evaluate_messages_test(
            elasticsearch_host_name=self.deployment.get_elasticsearch_hostname(),
            test_id=test_id,
            start_time=start_time,
            run_time=self.test_config.run_time,
            test_result=test_result,
            expected_message_count=1,
            recipient_sender_mapping=self.bootstrap_verification_mapping,
            evaluation_interval=self.test_config.evaluation_interval,
            range_name=self.deployment.get_range_name(),
        )
        # append the test result here
        self.test_results.append(myResult)

    ###
    # Print methods
    ###

    def print_report(self) -> None:
        """
        Purpose:
            Print the report for the test with results
        Args:
            N/A
        Returns:
            N/A
        """

        click.echo(f"Test Details:")
        click.echo(f"\tdeployment_name: {self.deployment.config['name']}")
        click.echo(
            f"\tnetwork manager plugin in deployment: {self.deployment.config.network_manager_kit.name}"
        )
        click.echo(
            f"\tcomms channels in deployment: {[x.name for x in self.deployment.config.comms_channels]}"
        )
        click.echo(f"\tclients: {self.clients}")
        click.echo(f"\tservers: {self.servers}")
        click.echo(f"\trun_time: {self.test_config.run_time}")
        click.echo(f"\tdelay_start: {self.test_config.delay_start}")
        click.echo(f"\tdelay_execute: {self.test_config.delay_execute}")
        click.echo(f"\tdelay_evaluation: {self.test_config.delay_evaluation}")
        click.echo(f"\tevaluation_interval: {self.test_config.evaluation_interval}")
        click.echo(f"\tis_running: {self.test_config.is_running}")
        click.echo(f"\tno_down: {self.test_config.no_down}")
        click.echo(
            f"\tnetwork_manager_bypass: {self.test_config.network_manager_bypass}"
        )
        if self.test_config.network_manager_bypass:
            click.echo(
                f"\tcomms_channel being tested: {self.test_config.comms_channel}"
            )
            click.echo(
                f"\tcomms_channel_type being tested: {self.test_config.comms_channel_type}"
            )

        for test_result in self.test_results:
            print_single_test_case_report(test_result_to_print=test_result)


###
# General Utility Functions
###


# used by print report and send auto/manual
def print_single_test_case_report(
    test_result_to_print: TestResult,
) -> bool:
    """
    Purpose:
        Print a single test case report

        Meant to be called each time a test case is ready to be printed/reported
    Args:
        The TestResult that is to be printed
    Returns:
        A boolean value that returns true if all cases evaluate to true/passed
    """
    click.echo(f"{test_result_to_print.test_case} Test Results:")
    click.echo(
        f"\t{test_result_to_print.test_case} Tests Passed: {test_result_to_print.passed}"
    )
    click.echo(
        f"\t{test_result_to_print.test_case} Tests Failed: {test_result_to_print.failed}"
    )
    if test_result_to_print.failed:
        click.echo(f"\t{test_result_to_print.test_case} Failures:")
        for failed_expectation in sorted(test_result_to_print.failed_expectations):
            click.echo(f"\t\t{failed_expectation}")
        # Printing report determined that case has failed
        return False

    # Printing report determined that case has passed
    return True


# used by verify & timeout
def evaluate_messages_test(
    elasticsearch_host_name: str,
    test_id: str,
    start_time: int,
    run_time: int,
    test_result: TestResult,
    expected_message_count: int,
    recipient_sender_mapping: dict,
    expected_message_size: int = None,
    evaluation_interval: int = 5,
    range_name: str = None,
) -> None:
    """
    Purpose:
        Evaluate message related tests and return results

        Evaluates tests at the sender/receiver pair level. Message hashes, count and size must
        match for the sender/receiver pair to be considered passed.
    Args:
        elasticsearch_host_name: name for creating elastic search connection/queries
        test_id: Test ID set for messages
        start_time: Time the test was kicked off
        run_time: Time the test will run for
        test_result: Object to store test results
        expected_message_count: expected number of messages sent between sender/receiver pairs
        recipient_sender_mapping: mapping of sender/receiver pairs
        expected_message_size: expected size of messages (used for auto messages only)
        evaluation_interval: how often to query the elasticsearch while looping
        range_name: name of range
    Returns:
        N/A
    """

    ### TODO: check what the actual byte size is
    if expected_message_size != None and expected_message_size < 30:
        logger.warning(
            "Message size verification is disabled because message overhead may be over 30 bytes"
        )
        expected_message_size = None

    warnings.filterwarnings("ignore", category=ElasticsearchWarning)
    es = Elasticsearch(elasticsearch_host_name)
    query = elasticsearch_utils.create_query(
        actions=["sendMessage", "receiveMessage"],
        # We need to search 5+ seconds prior to first send because of
        # the Android timing bug RACE2-2211
        time_range=[["gt", f"{start_time - 5000}"]],
        range_name=range_name,
    )

    end_time = (start_time / 1000) + run_time

    is_test_over = False
    while not is_test_over:
        msg_count = {}  # {"sender->recipient": msg count}
        is_test_over = time.time() > end_time
        temp_test_result = deepcopy(test_result)
        # Query elasticsearch for new traces
        results = elasticsearch_utils.do_query(es=es, query=query)
        spans = elasticsearch_utils.get_spans(es, results)
        (
            source_persona_to_span,
            trace_id_to_span,
        ) = elasticsearch_utils.get_message_spans(spans)

        for recipient, senders in recipient_sender_mapping.items():
            # spans_from_recipient_node include sendMessage and receiveMessage spans from multiple
            # tests
            spans_from_recipient_node = source_persona_to_span.get(recipient, [])

            for receive_span in spans_from_recipient_node:
                if (
                    receive_span["messageTestId"] != test_id
                    or receive_span["messageTo"] != recipient
                ):
                    # filter spans so we are left with receiveMessage from this test created on
                    # the recipient persona only
                    continue
                # There should be 2 spans with matching trace ids, the receiveMessage span from the
                # recipient and the sendMessage span from the sender
                matching_trace_spans = trace_id_to_span.get(
                    receive_span["trace_id"], []
                )
                for span in matching_trace_spans:
                    if span["source_persona"] != receive_span["messageFrom"]:
                        # ignore the receiveMessage span we got the trace id from earlier
                        continue
                    if span["messageHash"] != receive_span["messageHash"]:
                        # confirm message hash is the same on send/receive spans
                        continue
                    if (
                        expected_message_size
                        and int(span["messageSize"]) != expected_message_size
                    ):
                        # for auto messages check the size
                        continue
                    # sender span found for given receive span, add to message count for
                    # sender/receiver pair
                    message_key = f"{receive_span['messageFrom']}->{recipient}"
                    msg_count.setdefault(message_key, 0)
                    msg_count[message_key] += 1

            # Verify expected message count for sender->receiver pair now that all spans for the
            # receiver have been acounted for
            for sender in senders:
                message_key = f"{sender}->{recipient}"
                temp_test_result.total += 1
                if (
                    msg_count.get(message_key)
                    and msg_count[message_key] == expected_message_count
                ):
                    temp_test_result.passed += 1
                else:
                    temp_test_result.failed += 1
                    msg_count.setdefault(message_key, 0)
                    actual_message_matches = msg_count[message_key]
                    temp_test_result.failed_expectations.append(
                        f"{message_key}: msg count: expected {expected_message_count}, "
                        f"actual {actual_message_matches}"
                    )

        # End test if all passed or if time is up
        if is_test_over or temp_test_result.total == temp_test_result.passed:
            test_result = deepcopy(temp_test_result)
            break
        time.sleep(evaluation_interval)

    return test_result
