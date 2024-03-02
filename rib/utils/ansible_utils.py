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
        Utilities for leveraging Ansible from RiB
"""

# Python Library Imports
import getpass
import json
import logging
import os
import pexpect
import re
import time
from datetime import timedelta
from pathlib import Path
from typing import Any, AnyStr, Dict, List, Optional


# Local Library Imports
from rib.utils import error_utils, general_utils


logger = logging.getLogger(__name__)


###
# Ansible Playbook Functions
###


def run_playbook(
    playbook_filename: str,
    playbook_vars: Optional[Dict[str, Any]] = None,
    ssh_key_name: Optional[str] = None,
    hosts: Optional[List[str]] = None,
    inventory_file: Optional[str] = None,
    limit: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    fail_on_error: bool = True,
    remote_username: Optional[str] = None,
    secrets: Optional[List[str]] = None,
    timeout: int = 120,
    num_forks: int = 5,
    dry_run: bool = False,
    verbosity: int = 0,
) -> None:
    """
    Purpose:
        Run a specified Ansible playbook with the provided env and vars.

        # TODO, using pexepct not the api because ansible says that is unsage. pexpect
        is also unsafe, so really we need to think about this and maybe refactor to
        the ansible api
    Args:
        playbook_filename: filename of the playbook to run. will be an absolute link
        playbook_vars: vars to pass the playbook for execution
        ssh_key_name: private key name to use to authenticate
        hosts: list of hosts to run the playbook on. If no hosts or inventory file is
            specified, then the playbook will be run on localhost.
        inventory_file: path to inventory file, if no hosts are specified. If no hosts or
            inventory file is specified, then the playbook will be run on localhost.
        limit: limit to subset of inventory
        env: env of the shell environment to run `ansible-playbook`
        fail_on_error: Whether to raise if playbook fails
        remote_username: remote user for the command
        secrets: text that should not be written to console (e.g., access tokens)
        timeout: how long to allow the playbook to run before timing out
        num_forks: Number of forks for running ansible playbooks. Will help
            with larger distributed tasks (like starting n workers when n is large)
        dry_run: Run playbook in check mode
        verbosity: level of verbosity for the command
    Return:
        N/A
    Raises:
        error_utils.RIB801: If the playbook times out and does not complete
        error_utils.RIB800: If the playbook is run and fails tasks for some reason
    """

    logger.debug(f"Running Playbook: {playbook_filename}")

    # Set Verbosity Arg
    verbosity_arg = ""
    if verbosity >= 4:
        verbosity_arg = "-vvvv"
    elif verbosity >= 3:
        verbosity_arg = "-vvv"
    elif verbosity >= 2:
        verbosity_arg = "-vv"
    elif verbosity >= 1:
        verbosity_arg = "-v"

    # Set hosts arg if a list is provided. localhost is default and needs no value
    hosts_arg = ""
    if hosts:
        hosts_arg += f"-i {','.join(hosts)},"
    elif inventory_file:
        hosts_arg += f"-i {inventory_file}"

    limit_arg = ""
    if limit:
        limit_arg = f"-l {limit}"

    # Set hosts arg if a list is provided. localhost is default and needs no value
    private_key_arg = ""
    if ssh_key_name:
        private_key_arg += f"--private-key={ssh_key_name}"

    # Set username arg if one is provided.
    remote_username_arg = ""
    if remote_username:
        remote_username_arg += f"--user={remote_username}"

    check_arg = ""
    if dry_run:
        check_arg = "--check"

    # Create the command to run the ansible playbook
    run_playbook_command = [
        "ansible-playbook",
        f"{playbook_filename}",
        f"--forks={num_forks}",
        f"{private_key_arg}",
        f"{hosts_arg}",
        f"{limit_arg}",
        f"{remote_username_arg}",
        f"{verbosity_arg}",
        f"{check_arg}",
        "--extra-vars",
        f"'{json.dumps(playbook_vars)}'",
    ]

    logger.debug(
        AnsibleOutputLogger.mask(
            f"Playbook Command: {' '.join(run_playbook_command)}", secrets
        )
    )

    # Need a logger name-friendly version of the playbook file
    playbook_name = Path(playbook_filename).stem.replace("-", "_")

    # Spawn the process
    start_time = time.time()
    run_playbook_process = pexpect.spawn(
        " ".join(run_playbook_command),
        env=env,
        timeout=timeout,
    )
    run_playbook_process.logfile_read = AnsibleOutputLogger(
        logger.getChild(playbook_name), secrets
    )
    run_playbook_stdout = ""

    # Loop the command until it completes or timeout is reached
    while True:
        try:
            expect_idx = run_playbook_process.expect(
                [r"Enter passphrase for key", pexpect.EOF], timeout=timeout
            )
        except pexpect.exceptions.TIMEOUT as timeout_err:
            raise error_utils.RIB801(playbook_filename) from None

        # Getting command output
        if run_playbook_process.before:
            run_playbook_stdout += run_playbook_process.before.decode("utf-8")
        if run_playbook_process.after:
            if run_playbook_process.after != pexpect.EOF:
                run_playbook_stdout += run_playbook_process.after.decode("utf-8")

        if expect_idx == 0:
            ssh_key_pass = getpass.getpass(
                "SSH Key Password (Hit Enter if there is none): "
            )
            run_playbook_process.sendline(ssh_key_pass)
            continue
        else:
            break

    stop_time = time.time()
    duration = timedelta(seconds=stop_time - start_time)
    logger.trace(f"Playbook {playbook_filename} took {duration} to execute")

    # Check the output for errors/success/data
    failed_tasks = []
    num_tasks_failed = 0
    playbook_failed = False
    for stdout_line in run_playbook_stdout.split("\n"):
        playbook_error_search = re.search(r"(ERROR!).+", stdout_line)
        if playbook_error_search:
            playbook_failed = True

        failed_task_search = re.search(r"(fatal\:|unreachable\:).+", stdout_line)
        if failed_task_search:
            failed_tasks.append(failed_task_search.group(0))

        num_tasks_failed_search = re.search(r"failed=[0-9]+", stdout_line)
        if num_tasks_failed_search:
            num_tasks_failed += int(num_tasks_failed_search.group(0).split("=")[-1])

        num_hosts_unreachable_search = re.search(r"unreachable=[0-9]+", stdout_line)
        if num_hosts_unreachable_search:
            num_tasks_failed += int(
                num_hosts_unreachable_search.group(0).split("=")[-1]
            )

    # If a failure is found, raise a specific exception
    if fail_on_error:
        if playbook_failed:
            raise error_utils.RIB800(
                playbook_filename, 1, [run_playbook_stdout], verbose=True
            )
        elif num_tasks_failed:
            raise error_utils.RIB800(
                playbook_filename,
                num_tasks_failed,
                failed_tasks,
                verbose=True,  # For first launch, verbose errors
            )


###
# Ansible Playbook Functions
###


def load_playbook_var(playbook_var_filename: str) -> str:
    """
    Purpose:
        Load a playbook var that was stored to disk into memory and parse it. Ansible
        registers vars as json objects. stdout will hold the output of the command.
    Args:
        playbook_var_filename (str): filename of the playbook var to load
    Return:
        playbook_var (str): The loaded playbook var
    Raises:
        N/A
    """

    try:
        raw_playbook_var = general_utils.load_file_into_memory(
            playbook_var_filename, data_format="json"
        )
    except Exception as err:
        raise error_utils.RIB802(playbook_var_filename) from None

    return raw_playbook_var.get("stdout", None)


class AnsibleOutputLogger:
    """I/O-like writer that masks secrets and logs"""

    MASK_ENABLED = os.environ.get("ENVIRONMENT", "production") == "production"
    MASKED = "[MASKED]"

    def __init__(self, logger: logging.Logger, secrets: Optional[List[str]] = None):
        """
        Purpose:
            Initializes the writer
        Args:
            secrets: Texts to be masked
        """
        self.logger = logger
        self.secrets = secrets or []

    def flush(self) -> None:
        """
        Purpose:
            Does nothing, only exists to satisfy pexpect's logfile requirements
        Args:
            N/A
        Return:
            N/A
        """

    def write(self, msg: AnyStr) -> int:
        """
        Purpose:
            Logs the given message text, masking any secrets present in the message
        Args:
            msg: Message text
        Return:
            Number of bytes written
        """
        return self.logger.trace(self.mask(msg, self.secrets))

    @classmethod
    def mask(cls, text: AnyStr, secrets: Optional[List[str]]) -> AnyStr:
        """
        Purpose:
            Masks the secrets present in the given text, if any
        Args:
            text: Text to be masked
            secrets: Texts to be masked
        Return:
            Masked text
        """
        if not cls.MASK_ENABLED:
            return text

        masked_text = text
        # If input was bytes, convert it to a string
        if isinstance(masked_text, bytes):
            masked_text = masked_text.decode()
        if secrets:
            for secret in secrets:
                masked_text = masked_text.replace(secret, cls.MASKED)
        return masked_text
