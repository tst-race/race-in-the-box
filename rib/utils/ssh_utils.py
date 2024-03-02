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
        System Utilities for using SSH to interact with other services
"""

# Python Library Imports
import click
import getpass
import logging
import os
import paramiko
import pexpect
import scp
import socket
import timeout_decorator
from typing import Iterable, Tuple

# Local Library Imports
from rib.utils import error_utils


logger = logging.getLogger(__name__)
cached_ssh_keys = {}
RIB_PRIVATE_KEY_FILE = "/root/.ssh/rib_private_key"


###
# SSH Key Functions
###


def get_rib_ssh_key() -> paramiko.pkey.PKey:
    """
    Purpose:
        Returns the standard RiB SSH private key
    Returns:
        Private key object
    Raises:
        error_utils.RIB007: When the key could not be obtained
    """
    agent = paramiko.Agent()
    agent_keys = agent.get_keys()
    if agent_keys:
        logger.trace("Using key from ssh-agent")
        return agent_keys[0]
    return get_ssh_key_from_file(RIB_PRIVATE_KEY_FILE)[0]


def get_ssh_key_from_file(ssh_keyfile: str) -> Tuple[paramiko.pkey.PKey, str]:
    """
    Purpose:
        Take in a keyfile and get an SSH Key object that can be used to establish
        a cnnection. There are different keytpyes that paramiko supports, and this
        will try them all without having to ask the user what type of key they are
        using. If they are using an unsupported key, it will error.
    Args:
        ssh_keyfile: Filename of the key to load into a key obj
    Returns:
        ssh_key: obj representation of the key
        ssh_keytype: name of the type of key for later use if needed
    Raises:
        error_utils.RIB007: when the key type is not supported
        error_utils.RIB007: when a password is required
    """

    ssh_key_and_type = cached_ssh_keys.get(ssh_keyfile, None)
    if ssh_key_and_type:
        return ssh_key_and_type

    key_types = {
        "rsa": paramiko.rsakey.RSAKey,
        "dsa": paramiko.dsskey.DSSKey,
        "ec": paramiko.ecdsakey.ECDSAKey,
        "openssh": paramiko.ed25519key.Ed25519Key,
    }

    ssh_key = None
    ssh_keytype = None
    ssh_key_pass = None
    # Try first without any password
    for use_key_pass in (False, True):
        # If the first try without a password worked, use that
        if ssh_key:
            break

        if use_key_pass:
            ssh_key_pass = getpass.getpass("SSH Key Password: ")
            if not ssh_key_pass:
                raise error_utils.RIB006("SSH key requires a password")

        for key_type, key_class in key_types.items():
            try:
                ssh_key = key_class.from_private_key_file(
                    ssh_keyfile, password=ssh_key_pass
                )
                ssh_keytype = key_type
                break
            except paramiko.ssh_exception.PasswordRequiredException as err:
                raise error_utils.RIB006(err) from None
            except paramiko.ssh_exception.SSHException as err:
                if "checkints do not match" in str(err):
                    raise error_utils.RIB008(ssh_keyfile) from None
                continue  # This is a normal error for a different key type, continue trying
            except Exception as err:
                raise error_utils.RIB006(err) from None

    # If key is not found, raise an exception
    if not ssh_key:
        raise error_utils.RIB007(ssh_keyfile, list(key_types.keys())) from None

    cached_ssh_keys[ssh_keyfile] = (ssh_key, ssh_keytype)

    if ssh_key_pass:
        if click.confirm(
            "Would you like to add this key to ssh-agent to avoid password prompts for this session?"
        ):
            add_ssh_key(ssh_keyfile, ssh_key_pass)

    return (ssh_key, ssh_keytype)


def start_ssh_agent() -> None:
    """
    Purpose:
        Starts the ssh-agent if it is not already running
    Args:
        N/A
    Returns:
        N/A
    """
    (_, list_status) = pexpect.run("ssh-add -l", withexitstatus=1)
    # 0 = can communicate to agent, has keys
    # 1 = can communicate to agent, no keys
    # 2 = cannot communicate to agent
    if list_status > 1:
        logger.debug("Starting ssh-agent")
        auth_sock = os.environ.get("SSH_AUTH_SOCK", "/root/.ssh/keyring")
        (agent_out, agent_status) = pexpect.run(
            f"ssh-agent -a {auth_sock}", withexitstatus=1
        )
        if agent_status != 0:
            logger.warning(f"Unable to start ssh-agent ({agent_status}): {agent_out}")
    else:
        logger.trace("ssh-agent is already running")


def add_ssh_key(ssh_keyfile: str, ssh_key_pass: str) -> None:
    """
    Purpose:
        Adds the given private key file to the ssh-agent
    Args:
        ssh_keyfile: Path to private key file
        ssh_key_pass: SSH key passphrase
    Returns:
        N/A
    """
    try:
        start_ssh_agent()
        (add_out, add_status) = pexpect.run(
            f"ssh-add {ssh_keyfile}",
            events={r"Enter passphrase for": f"{ssh_key_pass}\n"},
            withexitstatus=1,
        )
        if add_status != 0:
            logger.warning(f"Unable to add SSH key ({add_status}): {add_out}")
    except Exception as e:
        logger.warning(f"Unable to add SSH key: {e}")


###
# SSH Client Functions
###


def connect_ssh_client(
    hostname: str,
    username: str,
    ssh_key: paramiko.pkey.PKey,
    port: int = 22,
    timeout: int = 10,
) -> paramiko.client.SSHClient:
    """
    Purpose:
        Create an ssh client to a specified host. Use the username provided
        and the loaded key
    Args:
        ssh_keyfile: Filename of the key to load into a key obj
        hostname: The hostname of the server to ssh into
        username: the username to ssh to the server with
        ssh_key: obj representation of the key to use
        port: The port of the server to ssh with
        timeout: Timeout of the connection
    Returns:
        ssh_client: obj representation of the ssh connection
    Raises:
        paramiko.ssh_exception.NoValidConnectionsError: when invalid host
        paramiko.ssh_exception.AuthenticationException: when bad auth
        socket.timeout: when timeout on connection
        error_utils.RIB006: for any other error
    """

    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            hostname=hostname,
            port=port,
            username=username,
            pkey=ssh_key,
            timeout=timeout,
        )
    except paramiko.ssh_exception.PasswordRequiredException as _:
        # key not accepted by server
        raise error_utils.RIB006("SSH key was not accepted by server")
    except paramiko.ssh_exception.NoValidConnectionsError as _:
        # cannot connect (not valid), pass up for better reporting
        raise
    except paramiko.ssh_exception.AuthenticationException as _:
        # Bad authentication, pass up for better reporting
        raise
    except socket.timeout as _:
        # cannot connect timeout, pass up for better reporting
        raise
    except Exception as err:
        # other errors, catch and wrap with RiB error
        raise error_utils.RIB006(err) from None

    return ssh_client


def disconnect_ssh_client(ssh_client: paramiko.client.SSHClient) -> None:
    """
    Purpose:
        Disconnect the ssh client from the remote server
    Args:
        ssh_client: obj representation of the ssh connection
    Returns:
        N/A
    Raises:
        error_utils.RIB006: if the close operation fails
    """

    try:
        ssh_client.close()
    except Exception as err:
        raise error_utils.RIB006(err) from None


def check_ssh_client_connected(ssh_client: paramiko.client.SSHClient) -> bool:
    """
    Purpose:
        Verify the ssh client is still connected
    Args:
        ssh_client (paramiko ssh client obj): obj representation of the ssh connection
    Returns:
        ssh_client_connected (Boolean): Whether the connection is still alive
    Raises:
        N/A
    """

    ssh_client_connected = False
    if ssh_client.get_transport() and ssh_client.get_transport().is_active():
        ssh_client_connected = True

    return ssh_client_connected


###
# Command Functions
###


def run_ssh_command(
    ssh_client: paramiko.client.SSHClient,
    command: str,
    timeout: int = 60,
    print_stdout: bool = False,
    check_exit_status: bool = False,
) -> Tuple[Iterable[str], Iterable[str]]:
    """
    Purpose:
        Disconnect from the remote server
    Args:
        ssh_client (paramiko.client.SSHClient): Object representation of the ssh
            connection.
        command: Command to run on the remote server.
        timeout: How long to wait (in seconds) for the command to
            complete. Defaults to 60 seconds.
        print_stdout: Flag to enable printing stdout of the command to
            stdout of the local terminal. Defaults to False.
        check_exit_status: Flag to enable raising an exception if the
            command returns a non-zero exit code. Defaults to False.
    Returns:
        Tuple[Iterable[str], Iterable[str]]: stdout and stderr of the command.
    Raises:
        error_utils.RIB006: Command timed out.
        error_utils.RIB006: An unkown error occurred while running the command.
    """

    stdout = ""
    stderr = ""
    try:
        ssh_channel = ssh_client.get_transport().open_session()
        ssh_channel.settimeout(timeout)
        # TODO: may be easier to display output if stdout and stderr are combined.
        # However, this will mess up calling functions that depend on grepping stderr.
        # ssh_channel.set_combine_stderr(True)
        ssh_channel.exec_command(command)

        RECV_BUFFER_SIZE = 128
        while True:
            output_data = ssh_channel.recv(RECV_BUFFER_SIZE)
            if not output_data:
                break
            output_data_str = output_data.decode("utf-8")
            if print_stdout:
                print(output_data_str, end="")
            stdout += output_data_str

        while True:
            output_data = ssh_channel.recv_stderr(RECV_BUFFER_SIZE)
            if not output_data:
                break
            output_data_str = output_data.decode("utf-8")
            if print_stdout:
                print(output_data_str, end="")
            stderr += output_data_str

        if check_exit_status and ssh_channel.recv_exit_status() != 0:
            raise Exception(f"failed to run ssh command: {command}\n{stdout}\n{stderr}")
    except paramiko.buffered_pipe.PipeTimeout as err:
        raise error_utils.RIB006(f"ssh command: timed out: {err}") from None
    except socket.timeout as err:
        raise error_utils.RIB006(f"ssh command: socket timed out: {err}")
    except Exception as err:
        raise error_utils.RIB006(err) from None

    return (stdout.splitlines(), stderr.splitlines())


###
# SCP Functions
###


def connect_scp_client(
    ssh_client: paramiko.SSHClient, timeout: int = 10
) -> scp.SCPClient:
    """
    Purpose:
        Create an SCP client from an existing/connected SSH client.
    Args:
        ssh_client (paramiko ssh client obj): obj representation of the ssh connection
        timeout (Int): Timeout of the connection
    Returns:
        scp_client (paramiko scp client obj): obj representation of the scp connection
    Raises:
        error_utils.RIB006: any failure on connection
    """

    try:
        scp_client = scp.SCPClient(ssh_client.get_transport(), socket_timeout=timeout)
    except Exception as err:
        raise error_utils.RIB006(err) from None

    return scp_client


def check_scp_client_connected(
    scp_client: scp.SCPClient,
    expected_remote_file: str = "~/.ssh/authorized_keys",
    tmp_local_file: str = "/tmp/scp_client_connection_test",
) -> bool:
    """
    Purpose:
        Verify the scp client is still connected
    Args:
        scp_client: obj representation of the scp connection
        expected_remote_file: Known file on host to verify existance and
            pullability on the remote host. Defaults to auth keys, since we are
            using SSH and that SHOULD be there
        tmp_local_file: Temporary file to locally store the remote file to.
            Making this settable for testing and other purposes. Also allows flexibility
            for permissions and filesystem differences.
    Returns:
        scp_client_connected: Whether the connection is still alive
    Raises:
        N/A
    """

    scp_client_connected = False
    if scp_client:
        # Delete file if it alreadys exists
        if os.path.isfile(tmp_local_file):
            os.remove(tmp_local_file)

        # Get remote file and store to local file
        scp_client.get(expected_remote_file, tmp_local_file)

        # Check new file exists, also remove it for future tests
        if os.path.isfile(tmp_local_file):
            # New file exists, so SCP is connected
            scp_client_connected = True
            os.remove(tmp_local_file)

    return scp_client_connected


def scp_file_or_dir(
    scp_client: scp.SCPClient, local_path: str, remote_path: str, timeout: int = 300
) -> None:
    """
    Purpose:
        SCP a file or dir to the remote host
    Args:
        scp_client: obj representation of the scp connection
        local_path: Path to local host to send to the remote host
        remote_path: Path to remote host to store the file
        timeout: timeout for put operation. defaults to 5 mins
    Returns:
        N/A
    Raises:
        error_utils.RIB006: When the operation fails or times out
    """

    @timeout_decorator.timeout(timeout)
    def timeout_scp_put(
        scp_client: scp.SCPClient, local_path: str, remote_path: str
    ) -> None:
        """
        Purpose:
            wrap the put call with a timeout
        Args:
            scp_client: obj representation of the scp connection
            local_path: Path to local host to send to the remote host
            remote_path: Path to remote host to store the file
        Returns:
            N/A
        Raises:
            error_utils.RIB006: When the operation fails or times out
        """

        scp_client.put(local_path, remote_path, recursive=True)

    try:
        timeout_scp_put(scp_client, local_path, remote_path)
    except Exception as err:
        raise error_utils.RIB006(err) from None
