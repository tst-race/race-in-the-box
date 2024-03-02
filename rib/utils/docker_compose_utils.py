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
        Utilities for interfacing with RiB deployments
"""

# Python Library Imports
import re
import pexpect
from datetime import datetime
from typing import Any, Dict, List, Optional


# Local Python Library Imports
from rib.utils import error_utils


###
# Action Functions
###


def run_docker_compose_up(
    deployment_name: str,
    deployment_mode: str,
    docker_compose_file: str,
    env: Optional[Dict[str, str]] = None,
    services: Optional[List[str]] = None,
    timeout: int = 120,
    verbosity: int = 0,
) -> None:
    """
    Purpose:
        Run `docker-compose up -d` and handle input/output
    Args:
        deployment_name: name of the deployment being operated on, used for error reporting
        deployment_mode: mode of the deployment being operated on, used for error reporting
        docker_compose_file: filename of the docker-compose file generated for RiB
        env: environment variables to use in system calls
        services: optional list of services to be included in "up" command
        timeout: timeout in seconds for the up operation
        verbosity: level of verbosity for the command
    Return:
        N/A
    """

    start_command = ["docker-compose", f"--file={docker_compose_file}", "up", "-d"]

    if services:
        start_command += services

    if verbosity > 0:
        print(f"docker-compose command: {' '.join(start_command)}")

    start_process = pexpect.spawn(" ".join(start_command), env=env, timeout=timeout)
    start_stdout = ""

    print_progress_message_interval = 15
    last_time_progress_message_printed = datetime.now()
    # Loop the command until it completes or timeout is reached
    while True:
        expected_patterns = [r"\[yN\]", pexpect.EOF, "Downloading", "Extracting"]
        try:
            expect_idx = start_process.expect(expected_patterns, timeout=timeout)
        except pexpect.exceptions.TIMEOUT:
            break

        if start_process.before:
            start_stdout += start_process.before.decode("utf-8")
        if start_process.after:
            if start_process.after != pexpect.EOF:
                start_stdout += start_process.after.decode("utf-8")

        if expect_idx == 0:
            start_process.sendline("y")
        elif expect_idx in (2, 3):
            if (
                datetime.now() - last_time_progress_message_printed
            ).seconds > print_progress_message_interval:
                last_time_progress_message_printed = datetime.now()
                print(f"{expected_patterns[expect_idx]} docker images...")
            continue
        else:
            break  # Process Complete

    docker_login_failure = False
    docker_network_failure = False
    existing_containers = []
    images_not_found = []
    unhandled_errors = []
    for stdout_line in start_stdout.split("\n"):
        if "denied: access forbidden" in stdout_line:
            docker_login_failure = True
        elif "is already in use by container" in stdout_line:
            existing_containers.append(
                re.search(r"The container name \"\/(.*)\" is", stdout_line).group(1)
            )
        elif "manifest unknown" in stdout_line:
            # Newer versions of docker-compose simplified the output and now doesn't include
            # the name of the image that doesn't exist...
            match = re.search(r"manifest for (.*) not found", stdout_line)
            if match:
                images_not_found.append(match.group(1))
            else:
                images_not_found.append(
                    f"Failed to parse image name. Check this file: {docker_compose_file}"
                )
        elif (
            "denied: requested access" in stdout_line
            and "pull access denied for " in stdout_line
        ):
            images_not_found.append(
                re.search(r"pull access denied for ([^,]*),", stdout_line).group(1)
            )
        elif "IPv4 address pool among" in stdout_line:
            # Full Error
            # could not find an available, non-overlapping IPv4 address pool
            # among the defaults to assign to the network
            docker_network_failure = True
        elif "ERROR" in stdout_line:
            unhandled_errors.append(start_stdout)
            break

    if existing_containers:
        existing_containers = sorted(list(set(existing_containers)))
        error_msg = f"Containers already exist: {', '.join(existing_containers)}"
        raise error_utils.RIB304(deployment_name, deployment_mode, error_msg)

    if docker_login_failure:
        raise error_utils.RIB200()

    if docker_network_failure:
        raise error_utils.RIB209()

    if images_not_found:
        raise error_utils.RIB208(images_not_found)

    if unhandled_errors:
        raise error_utils.RIB306(deployment_name, "up", unhandled_errors)


def run_docker_compose_stop(
    deployment_name: str,
    docker_compose_file: str,
    env: Dict[Any, Any] = None,
    services: Optional[List[str]] = None,
    timeout: int = 120,
    verbosity: int = 0,
) -> None:
    """
    Purpose:
        Run `docker-compose stop` and handle input/output
    Args:
        deployment_name: name of the deployment being operated on, used
            for error reporting
        docker_compose_file: filename of the docker-compose file
            generated for RiB
        env: environment variables to use in system calls
        services: optional list of services to be included in "stop" command
        timeout: timeout in seconds for the down operation
        verbosity: level of verbosity for the command
    Return:
        N/A
    """

    # Set the env default if it is not passed in
    if not env:
        env = {}

    stop_command = ["docker-compose", f"--file={docker_compose_file}", "stop"]

    if services:
        stop_command += services

    if verbosity > 0:
        print(f"docker-compose command: {' '.join(stop_command)}")

    stop_process = pexpect.spawn(" ".join(stop_command), env=env, timeout=timeout)
    stop_stdout = ""

    while True:
        try:
            expect_idx = stop_process.expect([r"\[yN\]", pexpect.EOF], timeout=timeout)
        except pexpect.exceptions.TIMEOUT:
            failed_message = stop_process.before
            raise error_utils.RIB311(deployment_name, "stop", failed_message) from None

        if stop_process.before:
            stop_stdout += stop_process.before.decode("utf-8")
        if stop_process.after:
            if stop_process.after != pexpect.EOF:
                stop_stdout += stop_process.after.decode("utf-8")

        if expect_idx == 0:
            stop_process.sendline("y")
        else:
            break  # Process Complete

    stop_errors = []
    for stderr_line in stop_stdout.split("\n"):
        if stderr_line.startswith("ERROR:"):
            if stderr_line not in stop_errors:
                stop_errors.append(stderr_line)

    unhandled_errors = []
    for start_error in stop_errors:
        unhandled_errors.append(start_error)
    if unhandled_errors:
        raise error_utils.RIB306(deployment_name, "stop", unhandled_errors)


def run_docker_compose_remove(
    deployment_name: str,
    docker_compose_file: str,
    env: Dict[Any, Any] = None,
    services: Optional[List[str]] = None,
    timeout: int = 120,
    verbosity: int = 0,
) -> None:
    """
    Purpose:
        Run `docker-compose remove` and handle input/output
    Args:
        deployment_name: name of the deployment being operated on, used
            for error reporting
        docker_compose_file: filename of the docker-compose file
            generated for RiB
        env: environment variables to use in system calls
        services: optional list of services to be included in "rm" command
        timeout: timeout in seconds for the remove operation
        verbosity: level of verbosity for the command
    Return:
        N/A
    """

    # Set the env default if it is not passed in
    if not env:
        env = {}

    remove_command = [
        "docker-compose",
        f"--file={docker_compose_file}",
        "rm",
        "--force",
    ]

    if services:
        remove_command += services

    if verbosity > 0:
        print(f"docker-compose command: {' '.join(remove_command)}")

    remove_process = pexpect.spawn(" ".join(remove_command), env=env, timeout=timeout)
    remove_stdout = ""

    while True:
        expect_idx = remove_process.expect([r"\[yN\]\:", pexpect.EOF])
        if remove_process.before:
            remove_stdout += remove_process.before.decode("utf-8")
        if remove_process.after:
            if remove_process.after != pexpect.EOF:
                remove_stdout += remove_process.after.decode("utf-8")

        if expect_idx == 0:
            remove_process.sendline("y")
        else:
            break  # Process Complete

    remove_errors = []
    for stderr_line in remove_stdout.split("\n"):
        if stderr_line.startswith("ERROR:"):
            if stderr_line not in remove_errors:
                remove_errors.append(stderr_line)

    unhandled_errors = []
    for start_error in remove_errors:
        unhandled_errors.append(start_error)
    if unhandled_errors:
        raise error_utils.RIB306(deployment_name, "remove", unhandled_errors)
