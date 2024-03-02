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
        Module to hold different types of RiB errors/warnings/etc.
"""

# Python Library Imports
import json
import os
import sys
from enum import Enum
from typing import Any, Collection, Dict, Iterable, List, Optional, Tuple

from rib.utils import general_utils


def get_message(err: Exception) -> str:
    """
    Purpose:
        Get an error message for the given exception
    Args:
        err: Exception
    Return:
        Message for the exception
    """

    if isinstance(err, RIB000):
        return err.msg
    return str(err)


###
# RIB0XX - General Exceptions
# RIB1XX - GitHub Exceptions
# RIB2XX - Docker Exceptions
# RIB3XX - Deployment Exceptions
# RIB4XX - Race Test App Exceptions
# RIB5XX - Kit/Plugin Exceptions
# RIB6XX - Test Exceptions
# RIB7XX - AWS Exceptions
# RIB8XX - Ansible Exceptions
# RIBaXX - Android (ADB) Exceptions
###


class RIB000(Exception):
    """
    Purpose:
        RIB000 is the base exception for all RiB errors. These will wrap exceptions
        that are caught during the execution of RiB to provide the user a better
        interaction with the tool instead of stack traces. Will extend this more
        for automatic error reporting to TA3, dumpting data into files, etc
    """

    def __init__(self):
        """
        Purpose:
            Initialization of the exception. will set the error URL and parse any
            other dynamic part of the configs. will also be repsonsible for automation
            of error reporting to TA3.
        """

        super().__init__()

        # Hiding Traceback from User if not in development environment
        # To set this, call rib with --dev
        if os.environ.get("ENVIRONMENT", None) != "development":
            sys.tracebacklimit = 0

    def __str__(self):
        """
        Purpose:
            String representation of the exception, will always show the code name,
            message, suggestion, and URL to get help if possible
        """

        default_msg = (
            "RiB has encountered an unknown error, please reach out "
            "to TA3 at (race@twosixlabs.com)"
        )

        return (
            f"\n"
            f"\tError Code: {self.__class__.__name__}\n"
            f"\tMessage: {getattr(self, 'msg') if hasattr(self, 'msg') else default_msg}\n"
            f"\tSuggestion: {getattr(self, 'suggestion') if hasattr(self, 'suggestion') else 'N/A'}\n"
        )


###
# General Exceptions
###


class RIB001(RIB000):
    """
    Purpose:
        RIB001 is for Not Implemented Features
    """

    suggestion = f"Check RiB version `rib --version` or email race@twosixlabs.com"

    def __init__(self, feature=None):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        if feature:
            self.msg = f"Feature Not Implemented: {feature}"
        else:
            self.msg = f"Feature Not Implemented"


class RIB002(RIB000):
    """
    Purpose:
        RIB002 occurs when the user enters a state in the RiB container/application
        that requires a restart of the container.
    """

    suggestion = "Restart RiB Container, if it persists email race@twosixlabs.com"

    def __init__(self, err):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"User State Error: {err}"


class RIB003(RIB000):
    """
    Purpose:
        RIB003 is for Invalid RACE Mode for the user
    """

    def __init__(self, rib_mode):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Invalid RACE Mode: {rib_mode}"
        self.suggestion = "Rerun command with `--mode=(local|t_e|aws)`"


class RIB004(RIB000):
    """
    Purpose:
        RIB004 is for Invalid RiB State for the user, need to run init
    """

    def __init__(self, invalid_state_reason=None):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        if invalid_state_reason:
            self.msg = f"Invalid RiB State: {invalid_state_reason}"
        else:
            self.msg = "Invalid RiB State"

        self.suggestion = "Run command `rib config init --help` to get params and rerun `rib config init`"


class RIB005(RIB000):
    """
    Purpose:
        RIB005 is for Incompatible versions of RACE
    """

    def __init__(self, race_version):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Incompatible version of RACE: {race_version}"
        self.suggestion = (
            "Upgrade/Downgrade RiB to a version that is compatible with the RACE"
            " version you are testing"
        )


class RIB006(RIB000):
    """
    Purpose:
        RIB006 is for a General error that occurs using RiB
    """

    def __init__(self, error_msg):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Error Occurred: {error_msg}"
        self.suggestion = (
            "Check the error, and rerun the command. If error persists, please reach out "
            "to TA3 at (race@twosixlabs.com)"
        )


class RIB007(RIB000):
    """
    Purpose:
        RIB007 is for an unsupported or unrecognized ssh key
    """

    def __init__(self, ssh_keyfile, compatible_key_types):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"The SSH key provided {ssh_keyfile} is not compatible with RiB. "
            f"Compatible key types include: {', '.join(compatible_key_types)}"
        )
        self.suggestion = "Please generate and utilize a compatible key type"


class RIB008(RIB000):
    """
    Purpose:
        RIB008 is for the incorrect password for an encrypted ssh key
    """

    def __init__(self, ssh_keyfile):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"The Password provided for SSH key ({ssh_keyfile}) is incorrect."
        self.suggestion = "Please check your password and retry"


class RIB010(RIB000):
    """
    Purpose:
        RIB010 is for an SSH key is not set or not correct permissions. Necessary
        for AWS Env and RiB Remote Deployment functionality
    """

    def __init__(self):
        super().__init__()

        self.suggestion = (
            "Rerun rib.sh with `--ssh=path/to/private/key` and rerun command"
        )
        self.msg = (
            "ssh private key in rib (/root/.ssh/rib_private_key) "
            "is not valid, cannot execute the command"
        )


class RIB011(RIB000):
    """
    Purpose:
        RIB011 is for a command that takes plugins and/or channels and has duplicates
    """

    def __init__(self):
        super().__init__()

        self.msg = "Duplicate Channels/Plugins arguments found"
        self.suggestion = "Check the plugin and channel args for duplicates and run the updated command"


class RIB012(RIB000):
    """
    Purpose:
        RIB012 is for development errors where code needs to be updated in order to correct
        the error (e.g., incomplete updates or refactoring)
    """

    def __init__(self, msg):
        super().__init__()

        self.msg = msg
        self.suggestion = "This error requires a code update"


###
# Git Exceptions
###


class RIB103(RIB000):
    """
    Purpose:
        RIB103 is for cloning an already existing repo
    """

    def __init__(self, repo):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Repository already exists, not cloning: {repo}"
        self.suggestion = "Run with --force if you want to delete and repull"


class RIB104(RIB000):
    """
    Purpose:
        RIB104 is for missing GitHub access token
    """

    def __init__(self):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = "No GitHub access token configured"
        self.suggestion = (
            "Run `rib github config --access-token`, then re-run the command"
        )


class RIB105(RIB000):
    """
    Purpose:
        RIB105 is for failure to read GitHub configuration JSON
    """

    def __init__(self, filename: str, error: str):
        """
        Purpose:
            Initialization of the exception
        Args:
            filename: Name of configuration file being read
            error: Read/parse error that occurred
        """

        super().__init__()

        self.msg = f"Unable to read {filename}: {error}"
        self.suggestion = "Re-run `rib github config` or manually fix errors in the file, then retry the operation"


class RIB106(RIB000):
    """
    Purpose:
        RIB106 is for failure to determine default race-core
    """

    def __init__(self, reason: str):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Unable to determine race-core: {reason}"
        self.suggestion = "Specify race-core explicitly, or re-run `rib github config` to set default race-core parameters"


class RIB107(RIB000):
    """
    Purpose:
        RIB107 is for failure to determine default image
    """

    def __init__(self, image: str, reason: str):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Unable to determine {image} image: {reason}"
        self.suggestion = "Specify image explicitly, or re-run `rib github config` to set default race-images parameters"


class RIB108(RIB000):
    """
    Purpose:
        RIB108 is for missing default GitHub organization
    """

    def __init__(self):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = "No default GitHub organization configured"
        self.suggestion = (
            "Re-run `rib github config` to set default GitHub organization"
        )


class RIB109(RIB000):
    """
    Purpose:
        RIB109 is for failed GitHub API requests
    """

    def __init__(self, details: str, status_code: int):
        """
        Purpose:
            Initialization of the exception.

        Args:
            details: Request details
            status_code: Request response status code
        """

        super().__init__()

        self.msg = f"GitHub API failed with response {status_code}: {details}"
        self.suggestion = (
            "Ensure request parameters are correct and GitHub access token "
            "is valid and re-run command"
        )


class RIB110(RIB000):
    """
    Purpose:
        RIB110 is for missing GitHub account username
    """

    def __init__(self):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = "No GitHub account username configured"
        self.suggestion = "Run `rib github config --username`, then re-run the command"


###
# Docker Exceptions
###


class RIB200(RIB000):
    """
    Purpose:
        RIB200 is for telling the user that they need to log into the
        container Registry to get images. This error can also be thrown
        if the image specified was not found.
    """

    def __init__(self):
        super().__init__()

        self.msg = "Could not retrieve image from Docker Container Registry"
        self.suggestion = (
            "Run `rib docker login` and rerun the command or check image exists"
        )


class RIB201(RIB000):
    """
    Purpose:
        RIB201 is for failing to log into docker container registry
    """

    def __init__(self):
        super().__init__()

        self.msg = "Docker Login Failed"
        self.suggestion = (
            "Verify token is correct "
            "`cat ~/.race/rib/user-state/rib.json | egrep token`. "
            "If it is not, regenerate and reinit RiB "
            "`rib config init`"
        )


class RIB202(RIB000):
    """
    Purpose:
        RIB202 is for general docker exceptions
    """

    def __init__(self, docker_err):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Docker Error: {docker_err}"
        self.suggestion = "Verify Docker status"


class RIB203(RIB000):
    """
    Purpose:
        RIB203 is for docker status failed
    """

    def __init__(self):
        super().__init__()

        self.msg = "Docker not running or in good status"
        self.suggestion = "Exit RiB, restart docker, and restart RiB"


class RIB204(RIB000):
    """
    Purpose:
        For exceptions when building a base docker image.
    """

    def __init__(self, err):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Building Base Docker Image Error: {err}"
        self.suggestion = (
            "The output should describe why the build failed (most are logic in"
            " the Dockerfile), make changes to the Dockerfile and rerun the build"
            " command."
        )


class RIB206(RIB000):
    """
    Purpose:
        RIB206 is for generic exceptions when using a base docker image to generate
        build outputs for a stub docker image.
    """

    def __init__(self, err):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Building Stub/Plugin Docker Image Error: {err}"
        self.suggestion = "Check dockerfile, mounts, and outputs and try again"


class RIB207(RIB000):
    """
    Purpose:
        RIB207 is for build commands failing
    """

    def __init__(self, cp_file_command, cp_file_output):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"Building Stub/Plugin Docker Image Error, failed to copy"
            f" {cp_file_command}: {cp_file_output}"
        )
        self.suggestion = "Check dockerfile, mounts, and outputs and try again"


class RIB208(RIB000):
    """
    Purpose:
        RIB208 is for when a docker image is not found (local or remote)
    """

    def __init__(self, docker_images):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Docker Images Not Found: {', '.join(docker_images)}"
        self.suggestion = (
            "Verify the dockerfile name and tag. Note that you may need to tag your "
            "image to match the name you provided."
        )


class RIB209(RIB000):
    """
    Purpose:
        For docker errors related to how Docker handles its networks. If Docker is out
        of networks (and IP space it reserves), ask the user to prune their networks and
        try again
    """

    def __init__(self):
        super().__init__()

        self.msg = f"Starting docker containers failed due to Docker Network Error"
        self.suggestion = "Run `docker network prune` and rerun command"


class RIB210(RIB000):
    """
    Purpose:
        RIB210 is for pushing a docker image but no results are found. This is a problem
        that needs to be investigated by the dev team.
    """

    def __init__(self, docker_image):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Failure to Push {docker_image}: No Results"
        self.suggestion = (
            "Check that the image exists locally and that you are logged into "
            "docker (run `rib docker login` and try again)"
        )


class RIB211(RIB000):
    """
    Purpose:
        RIB211 is for pushing a docker image failing with some error data
    """

    def __init__(self, docker_image, error_msg):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Failure to Push {docker_image}: {error_msg}"
        self.suggestion = "Read the error output"


class RIB212(RIB000):
    """
    Purpose:
        RIB212 is for when a docker tag manifest is not found in container registry when expected
    """

    def __init__(self, docker_tag: str):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"{docker_tag} not found in container registry"
        self.suggestion = "Verify the docker image/tag, check container registry, and rerun the command"


class RIB213(RIB000):
    """
    Purpose:
        RIB213 is for when tags for an image could not be found in the container registry
    """

    def __init__(self, message: Optional[str] = None):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = message
        self.suggestion = (
            "Verify image tags exist for the specified RACE version and verify rib has been"
            " properly configured by running `rib docker verify`"
        )


###
# Deployment Exceptions
###


class RIB300(RIB000):
    """
    Purpose:
        RIB300 is when a user performs an action on an deployment but none exist

        If not alternative deployments exist, return nothing. if they do,
        list them for the user
    """

    def __init__(self):
        super().__init__()

        self.msg = "No Deployments Found"
        self.suggestion = "Check your RiB Mode `rib config list` or create a deployment"


class RIB301(RIB000):
    """
    Purpose:
        RIB301 is when a deployment name is seen as invalid by the system. Can
        be due to mode, vesrion, num servers, or images.
    """

    def __init__(self):
        super().__init__()

        self.msg = "Error parsing deployment name"
        self.suggestion = "Verify deployment is valid"


class RIB302(RIB000):
    """
    Purpose:
        RIB302 is when a user performs an action on a non-existant deployment, and there
        are alternative options for the user to select from
    """

    def __init__(self, deployment_name, deployments):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        sorted_deployments = sorted(
            [deployment.config["name"] for deployment in deployments]
        )

        self.msg = f"Deployment '{deployment_name}' Not Found"
        self.suggestion = "Available Deployments:\n\t\t" + "\n\t\t".join(
            sorted_deployments
        )


class RIB303(RIB000):
    """
    Purpose:
        RIB303 is for unsupported configurations for deployments

        Examples: >20 servers, more clients than servers (locally), etc
    """

    def __init__(self, unsupported_reason):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Unsupported Deployment Configuration: {unsupported_reason}"
        self.suggestion = f"Update deployment configuration and try again"


class RIB304(RIB000):
    """
    Purpose:
        For corrupted RiB deployment state, need to stop and remove all of the previous
        containers and tell the user to rerun the command
    """

    def __init__(self, deployment_name, rib_mode, error_msg):
        super().__init__()

        self.msg = f"{deployment_name} failed to up: {error_msg}"
        self.suggestion = (
            f"Run `rib deployment {rib_mode} down --force --name={deployment_name}`, then "
            f"run `rib deployment {rib_mode} up --name={deployment_name}` again"
        )


class RIB305(RIB000):
    """
    Purpose:
        RIB305 is for trying to start/stop/up/down a deployment that is not in the
        expected state. up/down allow for --force, which is not available for
        start/stop.
    """

    def __init__(
        self,
        deployment_name,
        rib_mode,
        action,
        expected_state,
        current_state,
        apps_not_started=None,
        apis_not_responding=None,
        apps_started=None,
        expected_containers=None,
        running_containers=None,
        missing_containers=None,
        unexpected_containers=None,
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"{deployment_name} in '{current_state}' state but expected "
            f"'{expected_state}', cannot {action}"
        )

        if apps_not_started:
            self.msg += f"\n\tApps Not Started: {', '.join(apps_not_started)}"
        if apis_not_responding:
            self.msg += f"\n\tNodes not responding to API requests: {', '.join(apis_not_responding)}"
        if apps_started:
            self.msg += f"\n\tStarted Apps: {', '.join(apps_started)}"
        if expected_containers:
            self.msg += f"\n\tExpected Containers: {', '.join(expected_containers)}"
        if running_containers:
            self.msg += f"\n\tRunning Containers: {', '.join(running_containers)}"
        if missing_containers:
            self.msg += f"\n\tMissing Containers: {', '.join(missing_containers)}"
        if unexpected_containers:
            self.msg += f"\n\tUnexpected Containers: {', '.join(unexpected_containers)}"

        # Set Suggestion
        if action in ("up", "down"):
            self.suggestion = (
                f"Run `rib deployment {rib_mode} {action} --force "
                f"--name={deployment_name}` if you want to force the action"
            )
        elif action == "start":
            self.suggestion = (
                f"Run `rib deployment {rib_mode} up --force "
                f"--name={deployment_name}`, then run `rib "
                f"deployment {rib_mode} {action} --name={deployment_name}`"
            )
        elif action == "stop":
            self.suggestion = "There is nothing to stop as the RACE app is not running"


class RIB306(RIB000):
    """
    Purpose:
        RIB306 is for general failures when spinning up/down the containers for a local
        deployment
    """

    def __init__(self, deployment_name, action, unhandled_errors):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        unhandled_errors_str = " and ".join(unhandled_errors)

        self.msg = (
            f"Failed to {action} the containers for {deployment_name}: "
            f"{unhandled_errors_str}"
        )
        self.suggestion = (
            f"Read the error, and retry the command after making updates to the "
            "deployment as necessary. There is most likely an issue with the images, "
            "mounts, or containers. Look at the docker logs for each node, and "
            "retry if everything looks right. If the problem persists, reach out to TA3"
        )


class RIB307(RIB000):
    """
    Purpose:
        RIB307 is for invalid sender/recipient parameter value when using send command.

        This can be due to sender == recipient, incorrect network-manager-bypass setting, and
        non-existant nodes
    """

    def __init__(
        self,
        sender,
        recipient,
        available_nodes,
        is_network_manager_bypass,
        reason=False,
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        if reason:
            self.msg = (
                f"Cannot send message from {sender} to {recipient}: {reason}."
                " Note: node connectivity determined by deployment and if network-manager-bypass "
                f"is active (network-manager-bypass == {is_network_manager_bypass})"
            )
        else:
            self.msg = (
                f"Cannot send message from {sender} to {recipient}. {sender} can send "
                f"to {available_nodes}. Note: node connectivity determined by "
                f"deployment and if network-manager-bypass is active (network-manager-bypass == "
                f"{is_network_manager_bypass})"
            )

        self.suggestion = (
            f"Please run the command again with a connected node or "
            f"with --network-manager-bypass set to a channel, link, or connection ID."
        )


class RIB308(RIB000):
    """
    Purpose:
        RIB308 is for general failures when creating a deployment
    """

    suggestion = "Please email the dev team at race@twosixlabs.com"

    def __init__(self, deployment_name, unhandled_errors):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        # TODO, we should fix this so that unhandled_errors is either a string or
        # list, not both (its used differently throughout the code now)
        if isinstance(unhandled_errors, str):
            unhandled_errors_str = unhandled_errors
        else:
            unhandled_errors_str = "\n".join(unhandled_errors)

        self.msg = f"failed to create {deployment_name}: {unhandled_errors_str}"


class RIB309(RIB000):
    """
    Purpose:
        RIB309 is for deployments already exist
    """

    def __init__(self, deployment_name, rib_mode):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"{deployment_name} already exists"
        self.suggestion = (
            f"Run `rib deployment {rib_mode} remove --name={deployment_name}` "
            "to remove the deployment and rerun the command if you want to "
            "recreate the deployment."
        )


class RIB310(RIB000):
    """
    Purpose:
        RIB310 is for deployments config is not found or not valid. This usually
        occurs when RiB has a non-backwards compatible change and a new version of
        rib is trying to interact with an old/incompatible deployment. you should either
        pick another version of rib or remove and recreate it with this version of
        rib
    """

    def __init__(self, deployment_name):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"{deployment_name} config is not valid for this version of RiB"
        self.suggestion = (
            "Remove and recreate the deployment with this version of RiB or open "
            "an older compatible version to interact with the deployment"
        )


class RIB311(RIB000):
    """
    Purpose:
        RIB311 is for timing out deployment start/stop/remove command
    """

    def __init__(self, deployment_name, action, error_msg):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"{deployment_name} failed to {action}: {error_msg}"
        self.suggestion = "Read error message and make changes based on output."


class RIB312(RIB000):
    """
    Purpose:
        RIB312 is for when deployment commands are missing params

        Note: this is necessary instead of using Click functionality as
        each deployment type will have different params that are required
    """

    def __init__(self, rib_mode, missing_params):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"Failed to Create {rib_mode.title()} Deployment, Missing Params: "
            f"{', '.join(missing_params)} for --mode={rib_mode}"
        )
        self.suggestion = "Rerun create command with the missing params set"


class RIB315(RIB000):
    """
    Purpose:
        RIB315 is for when a deployment is in an error state. This occurs when
        more containers are running than expected, the wrong images are running (TODO)
        or other things that we should flag.

        Note: --force will not help here, as force is meant to proceed with a deployment
        that is partially up or down
    """

    def __init__(self, deployment_name, details=None):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"{deployment_name} is in an error state, cannot complete command"
        self.suggestion = (
            f"A deployment is in an error state when more containers are running than "
            f"expected, when a race_node is running against a different image than "
            f"expected, or something else is wrong with the deployment. Please verify "
            f"the action you are doing (is another/different deployment running?) stop "
            f"existing deployments with docker, then retry. Note, --force will not "
            f"complete the task, as errors are not automatically fixable.\n"
            f"{details}"
        )


class RIB316(RIB000):
    """
    Purpose:
        RIB316 is for when creating a deployment fails

        Note: this is necessary instead of using Click functionality as
        each deployment type will have different params that are required
    """

    def __init__(self, deployment_name, rib_mode, error_msg):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"Failed to Create {rib_mode.title()} deployment {deployment_name}: "
            f"{error_msg}"
        )
        self.suggestion = "Rerun create command after fixing issue"


class RIB317(RIB000):
    """
    Purpose:
        RIB317 is for trying to start/stop/up/down a deployment that is already in
        the desired state
    """

    def __init__(
        self,
        deployment_name,
        rib_mode,
        action,
        current_state,
        apps_not_started=None,
        apis_not_responding=None,
        apps_started=None,
        expected_containers=None,
        running_containers=None,
        missing_containers=None,
        unexpected_containers=None,
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"{deployment_name} already in '{current_state}' state, "
            f"no need to '{action}'"
        )

        if apps_not_started:
            self.msg += f"\n\tApps Not Started: {', '.join(apps_not_started)}"
        if apis_not_responding:
            self.msg += f"\n\tAPIs Not Responding: {', '.join(apps_not_started)}"
        if apps_started:
            self.msg += f"\n\tStarted Apps: {', '.join(apps_started)}"
        if expected_containers:
            self.msg += f"\n\tExpected Containers: {', '.join(expected_containers)}"
        if running_containers:
            self.msg += f"\n\tRunning Containers: {', '.join(running_containers)}"
        if missing_containers:
            self.msg += f"\n\tMissing Containers: {', '.join(missing_containers)}"
        if unexpected_containers:
            self.msg += f"\n\tUnexpected Containers: {', '.join(unexpected_containers)}"

        if action in ("up", "down"):
            self.suggestion = (
                f"Please run `rib deployment {rib_mode} {action} --force "
                f"--name={deployment_name}` if you want to "
                "force the action"
            )
        else:
            self.suggestion = (
                f"{action} is not forcible, cannot run this command with current state "
            )


class RIB318(RIB000):
    """
    Purpose:
        RIB318 is for a postcondition failing after taking an action
    """

    def __init__(
        self,
        deployment_name,
        rib_mode,
        action,
        current_state,
        desired_state,
        status_details=None,
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"{deployment_name} failed to {action}, currently in '{current_state}' "
            f"state, expected to be in `{desired_state}` state after command finished"
        )

        if status_details is not None:
            self.msg += f"\n{status_details}"

        self.suggestion = (
            f"Check the status/info of the deployment (i.e. `rib deployment {rib_mode} "
            f"status --name={deployment_name}`) and see why the deployment is "
            "in the state it is. Note that this command may have timed out, so the "
            "status may report correctly in a moment."
        )


class RIB320(RIB000):
    """
    Purpose:
        RIB320 is for trying to run a remote deployment command but bastion is not
        set
    """

    def __init__(self, deployment_name, rib_mode):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Cannot run {rib_mode} mode command, Bastion IP for the deployment is not set"
        self.suggestion = (
            f"please run `rib deployment update --mode={rib_mode} --name={deployment_name} "
            "--bastion=<YOUR BASTION IP>`, then rerun"
        )


class RIB321(RIB000):
    """
    Purpose:
        RIB321 is for no sender/recipients found for sending messages

        This can be due to trying to send to a server without network-manager-bypass or other
        simiar things
    """

    def __init__(self):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            "Failed to create a sender/recipient mapping with the specified command"
        )

        self.suggestion = (
            f"Please run the command again with a connected node or "
            f"with --network-manager-bypass set to a channel, link, or connection ID."
        )


class RIB322(RIB000):
    """
    Purpose:
        RIB322 is for invalid config change
    """

    def __init__(self, reason, suggestion):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Failed to update config because {reason}"

        self.suggestion = suggestion


class RIB323(RIB000):
    """
    Purpose:
        RIB323 is for using a RiB function on an unsupported RACE version

        e.g. creating a deployment in RiB 0.5.0 then trying to change logging.json
        which was only introduced in RACE 0.6.0
    """

    def __init__(self, deployment_name, rib_mode, action):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"Failed to {action} because the deployment is built on an older version"
            f" of RACE that does not support this functionality"
        )

        self.suggestion = (
            f"Recreate the deployment and try again. This can be done by using"
            f" `rib deployment info {rib_mode} --name={deployment_name}` to get"
            f" the command used to create it previously"
        )


class RIB324(RIB000):
    """
    Purpose:
        Multiple deployments of the same type are running.
    """

    def __init__(self, deployment_names: Iterable[str], rib_mode: str):
        super().__init__()

        self.msg = f"Multiple {rib_mode} deployments detected: " + ", ".join(
            deployment_names
        )

        self.suggestion = "Call `rib deployment {rib_mode} down --force` on all the active deployments: "
        for name in deployment_names:
            self.suggestion += (
                f"`rib deployment {rib_mode} down --force --name={name}` "
            )

        super().__init__()


class RIB325(RIB000):
    """
    Purpose:
        Rotate Logs Failed
    """

    def __init__(self, deployment_name: str, script_stdout: List[str]):
        super().__init__()

        self.msg = f"Rotating {deployment_name} logs failed: {script_stdout}"

        self.suggestion = (
            "Read the output and make changes as necessary. Reach out to Two Six Labs "
            "if the problem persists and does not go away on retry"
        )

        super().__init__()


class RIB329(RIB000):
    """
    Purpose:
        RIB329 is for missing global config files

        This can be due to specifying an incorrect global config directory when upping a deployment
    """

    def __init__(self, directory, missing):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"Global configuration directory {directory} is missing "
            f"the following files: {' '.join(missing)}"
        )

        self.suggestion = "Create or copy the missing files"


class RIB331(RIB000):
    """
    Purpose:
        RIB331 is for attempted actions (start/stop/up/down) on deployment nodes that
        cannot be completed due to the current state of the targeted nodes.
    """

    def __init__(
        self,
        deployment_name: str,
        rib_mode: str,
        action: str,
        info: Optional[List[str]] = None,
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Unable to {action} any nodes"
        if info:
            for line in info:
                self.msg += f"\n\t\t{line}"

        self.suggestion = (
            f"Run `rib deployment {rib_mode} status -dd --name={deployment_name}` "
            "to check the status of specific nodes"
        )


class RIB332(RIB000):
    """
    Purpose:
        RIB332 is for a failed action performed against deployment nodes
    """

    def __init__(
        self,
        deployment_name: str,
        rib_mode: str,
        action: str,
        info: Optional[List[str]] = None,
    ):
        super().__init__()

        self.msg = f"{deployment_name} failed to {action} requested nodes"
        if info:
            for line in info:
                self.msg += f"\n\t\t{line}"

        self.suggestion = (
            f"Run `rib deployment {rib_mode} status -dd --name={deployment_name}` "
            "to check the status of specific nodes"
        )


class RIB333(RIB000):
    """
    Purpose:
        RIB333 is for a failed plugin config generation
    """

    def __init__(
        self,
        deployment_name: str,
        rib_mode: str,
        message: str,
    ):
        super().__init__()

        self.msg = f"{deployment_name} failed to generate configs with the following error: {message}"

        self.suggestion = f"Please retry config generation with 'rib deployment {rib_mode} config generate --name={deployment_name} --force -v' to get more debug information"


class RIB334(RIB000):
    """
    Purpose:
        RIB334 is for race.json missing the `plugins` key

        User will need to update their race.json to have the
    """

    def __init__(self, name, path):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        example_race_json = {
            "bandwidth": "25700000",
            "latency": "1000",
            "debug": "false",
            "channels": [
                "twoSixDirectPython",
                "twoSixIndirectPython",
            ],
            "plugins": [
                {
                    "file_path": "libPluginNMClientTwoSixStub.so",
                    "plugin_type": "network-manager",
                    "file_type": "shared_library",
                    "node_type": "client",
                },
                {
                    "file_path": "libPluginNMServerTwoSixStub.so",
                    "plugin_type": "network-manager",
                    "file_type": "shared_library",
                    "node_type": "server",
                },
                {
                    "file_path": "PluginCommsTwoSixPython",
                    "plugin_type": "comms",
                    "file_type": "python",
                    "node_type": "any",
                    "python_module": "PluginCommsTwoSixPython.PluginCommsTwoSixPython",
                    "python_class": "PluginCommsTwoSixPython",
                },
            ],
        }

        self.msg = (
            "Global configuration file requires `plugin` field with data necessary. "
            f"Example: {json.dumps(example_race_json, indent=4, sort_keys=True)}"
        )

        self.suggestion = (
            f"Update race.json located at {path} "
            f"and rerun the up deployment for {name}"
        )


class RIB335(RIB000):
    """
    Purpose:
        RIB335 is for plugin_cache changing in an unexpected way.

        User will need to recreate the deployment
    """

    def __init__(self, name, mode):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = "Plugins cache changed in an unexpected manor"

        self.suggestion = f"Please recreate the deployment. You can get the deployment create command from `rib deployment {mode} info --name{name}`"


class RIB336(RIB000):
    """
    Purpose:
        RIB336 is for invalid genesis/bootstrap node counts
    """

    def __init__(self, base_param, subset_param, comparison):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Invalid value for {subset_param}"
        self.suggestion = (
            f"Rerun the command with {base_param} value {comparison} {subset_param}"
        )


class RIB337(RIB000):
    """
    Purpose:
        RIB337 is for plugins with old-style artifact directories.

        This requires a change to the plugin itself in order to resolve.
    """

    def __init__(self, plugin_name, platforms: List[Tuple[str, str]]):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"The {plugin_name} plugin contains the following invalid artifact directories:"
        for old_dir, new_dir in platforms:
            self.msg += f"\n\t\t{old_dir} (should be {new_dir})"

        self.suggestion = "Contact the maintainer of this plugin to resolve."


class RIB338(RIB000):
    """
    Purpose:
        RIB338 is for prohibited bootstrap operations on deployments with no artifact manager plugins available.
    """

    def __init__(self, name):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Deployment {name} does not have any artifact manager plugins enabled. Cannot perform bootstrap operation."

        self.suggestion = "Recreate the deployment with an artifact manager plugin."


class RIB339(RIB000):
    """
    Purpose:
        RIB339 is for prohibited/unsupported pairs of node types in a bootstrap operation.
    """

    def __init__(
        self, introducer_type, introducer_persona, target_type, target_persona
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Bootstrapping {target_type} ({target_persona}) via {introducer_type} ({introducer_persona}) is not supported"

        self.suggestion = "Choose different introducer/target nodes, or re-run this command with --force"


class RIB340(RIB000):
    """
    Purpose:
        RIB340 is for trying to perform an operation on an AWS deployment but the host AWS
        environment is not ready
    """

    def __init__(
        self, deployment_name: str, aws_env_name: str, action: str, aws_env_status: Enum
    ):
        """
        Purpose:
            Initialization of the exception
        """

        super().__init__()

        self.msg = (
            f"Cannot {action} AWS deployment {deployment_name}, {aws_env_name} "
            f"AWS environment is not ready (status is {aws_env_status})"
        )
        self.suggestion = (
            f"Run `rib env aws status --name {aws_env_name} -dd` to get more information "
            "about the state of the AWS Environment"
        )


class RIB341(RIB000):
    """
    Purpose:
        RIB341 is for trying to perform an operation on a deployment that must be down,
        but the deployment is not actually down
    """

    def __init__(
        self,
        deployment_name: str,
        rib_mode: str,
        action: str,
        forcible: bool,
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Cannot {action} deployment {deployment_name}, it is not down"

        self.suggestion = (
            f"Check the status of the deployment by running `rib deployment {rib_mode} "
            f"status --name={deployment_name} -dd` or tear down the deployment by running "
            f"`rib deployment {rib_mode} down --name={deployment_name}`."
        )
        if forcible:
            self.suggestion += (
                " You can re-run the command with `--force` to force the operation."
            )


class RIB342(RIB000):
    """
    Purpose:
        RIB342 is for attempted actions on a deployment that cannot be completed
        because not all nodes are in the appropriate state
    """

    def __init__(
        self,
        deployment_name: str,
        rib_mode: str,
        action: str,
        reasons: Optional[Dict[str, Any]],
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"Unable to {action} deployment {deployment_name} because the following nodes are not "
            "in an appropriate state:"
        )
        if reasons:
            for node, reason in reasons.items():
                self.msg += f"\n\t\t{node}: {reason}"

        self.suggestion = (
            f"Run `rib deployment {rib_mode} status -dd --name={deployment_name}` "
            "to check the status of specific nodes"
        )


class RIB343(RIB000):
    """
    Purpose:
        RIB343 is for attempted actions on a deployment that is not the active deployment for the
        current mode/host environment
    """

    def __init__(
        self,
        deployment_name: str,
        rib_mode: str,
        action: str,
        active_deployment_name: Optional[str],
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        if active_deployment_name:
            self.msg = (
                f"Unable to {action} deployment {deployment_name} because another deployment is "
                f"already active: {active_deployment_name}"
            )

            self.suggestion = (
                f"Re-run the command against the active deployment, or run `rib deployment {rib_mode} "
                f"down --name={active_deployment_name}` to tear down the active deployment."
            )
        else:
            self.msg = (
                f"Unable to {action} deployment {deployment_name} because it is down"
            )
            self.suggestion = (
                f"Run `rib deployment {rib_mode} up --name={deployment_name}` to "
                "stand up the deployment"
            )


class RIB344(RIB000):
    """
    Purpose:
        RIB344 is for attempts to prepare a bridge device using a non-bridged node persona
    """

    def __init__(self, persona: str):
        """
        Purpose:
            Initializes the exception.
        Args:
            persona: Attempted node persona
        """

        super().__init__()

        self.msg = (
            f"Unable to prepare bridged device with non-bridged node persona {persona}"
        )
        self.suggestion = "Use a persona for a bridged node in the deployment"


class RIB345(RIB000):
    """
    Purpose:
        RIB345 is for attempts to prepare a bridge device but the VPN server IP address is unknown
    """

    def __init__(self, rib_mode: str):
        """
        Purpose:
            Initializes the exception.
        Args:
            rib_mode: Deployment type
        """

        super().__init__()

        self.msg = "Unable to prepare bridged device, VPN server IP address is unknown"
        if rib_mode == "aws":
            self.suggestion = "Ensure host AWS environment is provisioned"
        elif rib_mode == "local":
            self.suggestion = (
                "Restart RiB with the `--ip-address` argument to set the local "
                "machine IP address"
            )


class RIB346(RIB000):
    """
    Purpose:
        RIB346 is for missing genesis node counts when bootstrap node counts specified
    """

    def __init__(self, genesis_node_type, bootstrap_node_type):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"No genesis {genesis_node_type}s specified but non-genesis "
            f"{bootstrap_node_type}s were requested"
        )
        self.suggestion = (
            f"Rerun the command with at least one genesis {genesis_node_type}"
        )


class RIB349(RIB000):
    """
    Purpose:
        RIB349 is for errors related to runtime configs.
    """

    def __init__(self, msg, suggestion):
        super().__init__()

        self.msg = f"Runtime configs error: {msg}"
        self.suggestion = suggestion


class RIB350(RIB000):
    """
    Purpose:
        RIB350 is for bad plugin identifier errors (e.g. multiple env, conflicting race versions, etc.)
    """

    def __init__(self, context: str, race_version: str, detail: str = ""):
        super().__init__()

        if not detail:
            self.msg = f'{context} \n\tbad plugin identifier error in "{race_version}" (e.g. multiple env, conflicting race versions, etc.)'
        else:
            self.msg = f'{context} \n\tbad plugin identifier error in "{race_version}" (e.g. multiple env, conflicting race versions, etc.)\n\t{detail}'
        self.suggestion = (
            f"<name>:<revision>:<race-version>:<env>\n"
            "\tDefaults:\n"
            "\t<name>:<revision>:<race-version>       -> <name>:<revision>:<race-version>:<deployment-env>\n"
            "\t<name>:<revision>:<env>                -> <name>:<revision>:<latest-race-version>:<env>\n"
            "\t<name>:<revision>                      -> <name>:<revision>:<latest-race-version>:<deployment-env>\n"
            "\t<name>:<env>                           -> <name>:latest:<latest-race-version>:<env>\n"
            "\t<name>                                 -> <name>:latest:<latest-race-version>:<deployment-env>\n"
        )


class RIB351(RIB000):
    """
    Purpose:
        RIB351 is for a regex parameter that does not match any nodes
    """

    def __init__(self, nodes: List[str]):
        super().__init__()

        self.msg = f"\tProvided nodes/regular expressions did not match any nodes in the deployment: \n\t\t\t{general_utils.stringify_nodes(nodes)}\n"
        self.suggestion = "\tPlease retry with updated regular expressions"


class RIB352(RIB000):
    """
    Purpose:
        RIB352 is for a time or offset that does not correlate to any timezone
    """

    def __init__(self):
        super().__init__()

        self.msg = f"\tProvided time argument did not have a valid timezone correlated with it\n"
        self.suggestion = "\tPlease retry with a different local time"


class RIB353(RIB000):
    """
    Purpose:
        Unsupported command.
    """

    def __init__(self):
        super().__init__()

        self.msg = f"\tCommand is not currently supported for the given configuration\n"
        self.suggestion = "\tIf you need support for this command/configuration please contact Two Six"


###
# Race Test App Exceptions
###


class RIB400(RIB000):
    """
    Purpose:
        An error that occurred while trying to start `racetestapp` on the RACE nodes
    """

    def __init__(self, details):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"An error occurred while starting the RACE test app: {details}"
        self.suggestion = (
            f"If you have recently run `rib deployment up ...` then the test "
            "application on the RACE nodes may not have had enough time to properly "
            "spin up. Please try re-running the same command you just ran. If the "
            "problem persists please check the logs and deployment status. If this "
            "does not provide useful info on the error then please contact TA3."
        )


class RIB401(RIB000):
    """
    Purpose:
        An error that occurred calling send message for a deployment without the
        proper argument
    """

    argument_mapping = {
        "message": "--message",
        "message_size": "--size",
        "message_quantity": "--quantity",
        "message_period": "--period",
    }

    def __init__(self, message_type, missing_data):
        super().__init__()

        # Set message and suggestion
        self.msg = (
            f"Missing Arg {self.argument_mapping[missing_data]} for "
            f"sending a {message_type} message"
        )
        self.suggestion = "Rerun the send command with the missing argument"


class RIB402(RIB000):
    """
    Purpose:
        An error that occurred while trying to stop/kill `racetestapp` on the RACE nodes
    """

    def __init__(self, details):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"An error occurred while stopping/killing the RACE test app: {details}"
        )
        self.suggestion = (
            "The app may not have been running on some nodes or there may be an "
            "issue with connectivity. Please read the error and logs to see if this "
            "is an issue and try to restart the deployment and try again."
        )


class RIB403(RIB000):
    """
    Purpose:
        An error that occurred while making
        some call to an API and getting a non-200 response
    """

    def __init__(self, status_code, response):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Got a non-200 response ({status_code}): {response}"
        self.suggestion = (
            "Either there is an issue with the API not running, the app being in a "
            "non-expected state, or some other connectivity issue. Please check the "
            "status of the deployment and the app on all nodes"
        )


class RIB404(RIB000):
    """
    Purpose:
        RiB attempted to start `racetestapp` on a node where it is already started.
    """

    def __init__(self, node):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"RACE test app is already started on node: {node}"
        self.suggestion = f"If this is unexpected please review your configuration or report this error. If this is expected then ignore this error."


class RIB405(RIB000):
    """
    Purpose:
        A request error occurred while contacting the racetestapp API
    """

    def __init__(self, node, err):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"Unable to execute API request to RACE test app on node {node}: {err}"
        )
        self.suggestion = f"If this is unexpected please review your configuration or report this error. If this is expected then ignore this error."


class RIB406(RIB000):
    """
    Purpose:
        An error that occurred while trying to bootstrap a new RACE node
    """

    def __init__(self, details):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"An error occurred while bootstrapping a node into the RACE network: {details}"
        self.suggestion = (
            "There may be an issue with connectivity or with the supplied options. "
            "Please read the error and logs to see if this "
            "is an issue and try to restart the deployment and try again."
        )


class RIB407(RIB000):
    """
    Purpose:
        An error connecting to the Redis instance
    """

    def __init__(self):
        """
        Purpose:
            Initialization of the exception.
        """

        self.msg = "An error occurred connecting to the Redis server."
        self.suggestion = "Try the command again or re-up the deployment environment."

        super().__init__()


class RIB408(RIB000):
    """
    Purpose:
        An error retrieving node status for a node
    """

    def __init__(self, persona: str, reason: str):
        """
        Purpose:
            Initialization of the exception.
        """

        self.msg = f"Unable to retrieve node status for {persona}: {reason}"
        self.suggestion = (
            "Read the error output and make updates as necessary. If the problem "
            "persists, please reach out to Two Six Labs"
        )

        super().__init__()


class RIB409(RIB000):
    """
    Purpose:
        An error retrieving app status for a node
    """

    def __init__(self, persona: str, reason: str):
        """
        Purpose:
            Initialization of the exception.
        """

        self.msg = f"Unable to retrieve app status for {persona}: {reason}"
        self.suggestion = (
            "Read the error output and make updates as necessary. If the problem "
            "persists, please reach out to Two Six Labs"
        )

        super().__init__()


class RIB410(RIB000):
    """
    Purpose:
        An error publishing an action command to a node
    """

    def __init__(self, persona: str, action: str, reason: str):
        """
        Purpose:
            Initialization of the exception.
        """

        self.msg = f"Unable to publish {action} command to {persona}: {reason}"
        self.suggestion = (
            "Read the error output and make updates as necessary. If the problem "
            "persists, please reach out to Two Six Labs"
        )

        super().__init__()


class RIB411(RIB000):
    """
    Purpose:
        An error occurred sending messages in a deployment
    """

    def __init__(self, reason: str):
        """
        Purpose:
            Initialization of the exception.
        """

        self.msg = reason
        self.suggestion = (
            "Read the error output and make updates as necessary. If the problem "
            "persists, please reach out to Two Six Labs"
        )

        super().__init__()


class RIB412(RIB000):
    """
    Purpose:
        An error publishing an action command to a set of nodes
    """

    def __init__(self, action: str, reasons: Dict[str, Any]):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Unable to publish {action} command to the following nodes:"
        for persona, reason in reasons.items():
            self.msg += f"\n\t{persona}: {reason}"

        self.suggestion = (
            "Read the error output and make updates as necessary. If the problem "
            "persists, please reach out to Two Six Labs"
        )


class RIB413(RIB000):
    """
    Purpose:
        Mismatch between active deployment (in redis) and set/unset action
    """

    def __init__(
        self,
        deployment_name: str,
        current_deployment_name: str,
        action: str,
    ):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = (
            f"Cannot {action} active deployment in redis for {deployment_name}, "
            f"{current_deployment_name} is set as active"
        )
        self.suggestion = f"Down {current_deployment_name} first and rerun command."


###
# Kit/Plugin Exceptions
###


class RIB500(RIB000):
    """
    Purpose:
        RIB500 is for unparseable source
    """

    def __init__(self, raw, reason):
        """
        Purpose:
            Initialization of the exception.

        Args:
            raw: Raw source string
            reason: Reason source is invalid
        """

        super().__init__()

        self.msg = f"Source cannot be parsed: {reason}\n\t\tFrom raw source: {raw}"
        self.suggestion = (
            "Correct the source argument and re-run the command.\n"
            "Run `rib help kit-source` for documentation on supported source values."
        )


class RIB501(RIB000):
    """
    Purpose:
        RIB501 is for invalid source
    """

    def __init__(self, raw, reason):
        """
        Purpose:
            Initialization of the exception.

        Args:
            raw: Raw source string
            reason: Reason source is invalid
        """

        super().__init__()

        self.msg = f"Source is invalid: {reason}\n\t\tFrom raw source: {raw}"
        self.suggestion = (
            "Correct the source argument and re-run the command.\n"
            "Run `rib help kit-source` for documentation on supported source values."
        )


class RIB503(RIB000):
    """
    Purpose:
        RIB503 is for failure to retrieve from source
    """

    def __init__(self, raw, reason):
        """
        Purpose:
            Initialization of the exception.

        Args:
            raw: Raw source string
            reason: Reason source is invalid
        """

        super().__init__()

        self.msg = f"Failed to retrieve: {reason}\n\t\tFrom raw source: {raw}"
        self.suggestion = "Confirm source is correct"


class RIB504(RIB000):
    """
    Purpose:
        RIB504 is for unrecognized/unsupported archive files
    """

    def __init__(self, file):
        """
        Purpose:
            Initialization of the exception.

        Args:
            file: Archive file
        """

        super().__init__()

        self.msg = f"Failed to extract {file}, file type is not supported"
        self.suggestion = "Confirm source is correct"


class RIB505(RIB000):
    """
    Purpose:
        RIB505 is for failure to determine kit name
    """

    def __init__(self, what: str):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Failed to determine kit name from {what} kit"
        self.suggestion = "Confirm source kit is correctly built"


class RIB506(RIB000):
    """
    Purpose:
        RIB506 is for duplicate plugins
    """

    def __init__(self, plugin_or_channel: str, name: str):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Duplicate {plugin_or_channel} name found: {name}"
        self.suggestion = "Correct the plugin source selections and re-run the command"


class RIB507(RIB000):
    """
    Purpose:
        RIB507 is for failure to determine comms channel names
    """

    def __init__(self, what: str):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Failed to determine comms channels names from {what} kit"
        self.suggestion = "Confirm source kit is correctly built"


class RIB508(RIB000):
    """
    Purpose:
        RIB508 is for channels or components missing a providing kit
    """

    def __init__(self, what: str, missing: Iterable[str]):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"No comms kits selected that provide the following {what}(s): {' '.join(missing)}"
        self.suggestion = (
            "Correct the comms kit source selections and re-run the command"
        )


###
# Test Exceptions
###


class RIB600(RIB000):
    """
    Purpose:
        RIB600 is for an invalid test plan file
    """

    def __init__(self, reason):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        # Setting Message
        self.msg = f"Test Plan is invalid: {reason}"

        # Setting Suggestion
        self.suggestion = (
            "Please update the test plan to match the expected specification"
        )


class RIB601(RIB000):
    """
    Purpose:
        RIB601 is a failed test run, raised if --raise-on-fail is set
        when testing to allow for better automation
    """

    def __init__(self, deployment_name, race_test):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        total_failures = race_test.total_failed
        total_tests = race_test.total_failed + race_test.total_passed

        self.msg = f"{total_failures}/{total_tests} tests failed for {deployment_name}"

        self.suggestion = (
            "Check the deployment, test, test cases, and RiB. You can "
            "also look at the logs (last run), or rerun the test with "
            "--debug to see the data in memory"
        )


class RIB602(RIB000):
    """
    Purpose:
        RIB602 is when trying to test a comms channel when the channel is not in the
        deployment
    """

    def __init__(self, deployment_name, comms_channel):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"{comms_channel} is not a valid channel in {deployment_name}"

        self.suggestion = "Choose a different channel or deployment"


class RIB603(RIB000):
    """
    Purpose:
        RIB603 is for an invalid test plan
    """

    def __init__(self, test_plan, reason):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"Test plan ({test_plan}) is not valid: {reason}"

        self.suggestion = "Update the test plan to be valid"


class RIB604(RIB000):
    """
    Purpose:
        RIB604 is for a failed message test
    """

    def __init__(self, rib_mode, deployment_name, message_type):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"{message_type} message verification failed"

        self.suggestion = (
            f"Messages may still be in transit. Try running `rib deployment {rib_mode} "
            f" message list --name={deployment_name}` or look at jaeger tracing"
        )


class RIB605(RIB000):
    """
    Purpose:
        RIB605 is for a failed get matching messages from elasticsearch
    """

    def __init__(self, rib_mode, deployment_name, message_match_source):
        """
        Purpose:
            Initialization of the exception.
        """

        super().__init__()

        self.msg = f"{message_match_source} return matching messages failed"

        self.suggestion = (
            f"Elasticsearch may have timed out. Try re-running rib deployment {rib_mode} "
            f" {message_match_source} --name={deployment_name}"
        )


###
# AWS Exceptions
###


class RIB700(RIB000):
    """
    Purpose:
        RIB700 is for general AWS error. Wil catch unhandled errors, these
        should be updated to new error types in the future
    """

    def __init__(self, err: str) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            err (str): Repr of the error that caused the issue
        """

        super().__init__()

        self.msg = f"AWS failure: {err}"

        self.suggestion = (
            "Read the error output and make updates as necessary. If the problem "
            "persists, please reach out to Two Six Labs"
        )


class RIB701(RIB000):
    """
    Purpose:
        RIB701 occurs with invalid credentials.
    """

    def __init__(self):
        super().__init__()

        self.msg = f"AWS creds invalid"
        self.suggestion = (
            "Check your access and secret key to ensure they are as expected. Correct "
            "and try again"
        )


class RIB702(RIB000):
    """
    Purpose:
        RIB701 occurs with credentials with invalid privileges to certain AWS services
    """

    def __init__(self, missing_privileges: List[str]) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            missing_privileges (List[str]): names of the AWS services that the user
                needs access to and does not have
        """

        super().__init__()

        self.msg = (
            f"AWS profile missing privileges to AWS " f"services: {missing_privileges}"
        )

        self.suggestion = (
            "Reach out to your DevOps team to update permissions for the user provided "
            "in aws to add privileges for the specified services in AWS and try again. "
            "these are necessary for AWS mode to work"
        )


class RIB703(RIB000):
    """
    Purpose:
        RIB703 occurs when a user has already configured  a profile and tries to
        reinit without setting --overwrite
    """

    def __init__(self):
        super().__init__()

        self.msg = f"AWS profile already exists, not creating"
        self.suggestion = (
            "If you want to overwrite the profile, please rerun `rib aws init` with "
            "the --overwrite flag set"
        )


class RIB704(RIB000):
    """
    Purpose:
        RIB704 occurs when an aws service is expected but not supported
    """

    def __init__(self, service_name: str) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            service_name (str): name of the aws service that is not supported
        """

        super().__init__()

        self.msg = f"AWS service not supported: {service_name}"

        self.suggestion = (
            f"If your aws_env relies on {service_name}, reach out to two six "
            "to discuss implementing support"
        )


class RIB705(RIB000):
    """
    Purpose:
        RIB705 is for when creating an AWS aws_env fails
    """

    def __init__(self, aws_env_name: str, error_msg: str) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name (str): name of the env that the user tried to create
            error_msg (str): Repr of the error that caused the failure
        """

        super().__init__()

        self.msg = f"Failed to Create AWS aws_env {aws_env_name}: {error_msg}"
        self.suggestion = "Rerun create command after fixing issue"


class RIB706(RIB000):
    """
    Purpose:
        RIB706 is for when the AWS profile is not set but the user is attempting to run
        AWS commands. need to init first
    """

    def __init__(self):
        super().__init__()

        self.msg = f"AWS profile has not been initialized, failing"
        self.suggestion = (
            "Run `rib aws init` and create the profile with valid "
            "aws credentials so that `rib aws` commands can connect to AWS"
        )


class RIB707(RIB000):
    """
    Purpose:
        RIB707 is when an unexpected aws_env already exists
    """

    def __init__(self, aws_env_name: str) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name (str): name of the env that the user specified and already
                exists
        """

        super().__init__()

        self.msg = f"{aws_env_name} already exists"
        self.suggestion = (
            f"Run `rib env aws remove --name={aws_env_name}` "
            "to remove the aws_env and rerun the command if you want to "
            "recreate the aws_env."
        )


class RIB708(RIB000):
    """
    Purpose:
        RIB708 is when a user performs an action on an aws_env but none exist
    """

    def __init__(self):
        super().__init__()

        self.msg = "No Environments Found"
        self.suggestion = "Check your configuration or create an aws_env"


class RIB709(RIB000):
    """
    Purpose:
        RIB709 is when a user performs an action on a non-existant aws_env, and there
        are alternative options for the user to select from
    """

    def __init__(self, aws_env_name: str, aws_envs: Collection[str]) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name (str): name of the env that the user specified
            aws_envs (List[str]): available environment
        """

        super().__init__()

        self.msg = f"{aws_env_name} Environment Not Found"
        self.suggestion = "Available Environments:\n\t\t" + "\n\t\t".join(
            sorted(aws_envs)
        )


class RIB710(RIB000):
    """
    Purpose:
        RIB710 is for when an AWS Environment is in an error state. This occurs when
        there is some issue getting cloudformation data or something is happening
        that is unexpected

        Note: --force will not help here, as force is meant to proceed with an
        aws_env that is partially up or down
    """

    def __init__(self, aws_env_name: str, details: Optional[List[str]] = None) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name (str): name of the env that is is in an error state
            details (List[str]): details of the error if they exist
        """

        super().__init__()

        self.msg = f"{aws_env_name} is in an error state, cannot complete command"
        self.suggestion = (
            f"A AWS Environemnt is in an error state when there is an issue connecting "
            f"to AWS to get information about what is running. Please check your "
            f"AWS Cloudformation data to see what is running, check your AWS profile, "
            f"and make sure that you have the permissions you should. If the problem "
            f"persists, please reach out to Two Six Labs."
            f" Note, --force will not "
            f"complete the task, as errors are not automatically fixable.\n"
            f"{details}"
        )


class RIB711(RIB000):
    """
    Purpose:
        RIB711 is for trying to up/down an AWS Environment that is already in
        the desired state
    """

    def __init__(self, aws_env_name: str, action: str, current_state: Enum) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name (str): name of the env that is being acted on
            action (RibAwsEnvState): string name of the action to report to user
            current_state (RibAwsEnvState Enum): The state the env is in
        """

        super().__init__()

        self.msg = (
            f"{aws_env_name} already in '{current_state}' state, "
            f"no need to '{action}'"
        )

        if action == "down":
            self.suggestion = (
                f"Please run `rib env aws down --force "
                f"--name={aws_env_name}` if you want to "
                "force the action"
            )
        elif action == "up":
            self.suggestion = (
                f"Up is not forcible. Please down the deployment and rerun force"
            )
        else:
            self.suggestion = "Please reachout to Two Six Labs for Questions"


class RIB712(RIB000):
    """
    Purpose:
        RIB712 is for a postcondition failing after taking an action on an AWS Env
    """

    def __init__(
        self, aws_env_name: str, action: str, current_state: Enum, desired_state: Enum
    ) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name (str): name of the env that is being acted on
            action (RibAwsEnvState): string name of the action to report to user
            current_state (RibAwsEnvState Enum): The state the env is in
            desired_state (RibAwsEnvState Enum): The state the env should be in
        """

        super().__init__()

        self.msg = (
            f"{aws_env_name} failed to {action}, currently in '{current_state}' "
            f"state, expected to be in `{desired_state}` state after command finished"
        )

        self.suggestion = (
            f"Check the status/info of the aws env (i.e. `rib env aws status --"
            f"name={aws_env_name} -dd`) and see why the aws env is in the state it is"
        )


class RIB713(RIB000):
    """
    Purpose:
        RIB713 is for trying to up/down an AWS Environment that is not in the
        expected state. down allows for --force, which is not available for up
    """

    def __init__(
        self, aws_env_name: str, action: str, expected_state: Enum, current_state: Enum
    ) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name (str): name of the env that is being acted on
            action (RibAwsEnvState): string name of the action to report to user
            expected_state (RibAwsEnvState Enum): The state the env should be in
            current_state (RibAwsEnvState Enum): The state the env is in
        """

        super().__init__()

        self.msg = (
            f"{aws_env_name} already in '{current_state}' state but expected "
            f"'{expected_state}'; cannot '{action}'"
        )

        if action == "down":
            self.suggestion = (
                f"Please run `rib env aws down --force "
                f"--name={aws_env_name}` if you want to "
                "force the action"
            )
        elif action == "up":
            self.suggestion = (
                f"Up is not forcible. Please down the deployment and rerun force"
            )
        else:
            self.suggestion = "Please reachout to Two Six Labs for Questions"

        self.msg = (
            f"{aws_env_name} in '{current_state}' state but expected "
            f"'{expected_state}', cannot {action}"
        )


class RIB714(RIB000):
    """
    Purpose:
        RIB714 is for a corrupt deployment. Needs to be manually removed
    """

    def __init__(self, aws_env_name: str, aws_env_path: str) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name (str): name of the env that is corrupted
            aws_env_path (str): Path to deployment in the rib docker filesystem
        """

        super().__init__()

        self.msg = f"Environment {aws_env_name} is corrupted; please recreate"
        self.suggestion = (
            f"Please manually remove the environment with `rm -rf {aws_env_path}` "
            "and recreate the envrionment"
        )


class RIB715(RIB000):
    """
    Purpose:
        RIB715 is for when a component fails to start during `rib env aws up` and we
        want to report it specifically to the user. They will need to down/up and check
        the error (and maybe reach out to us)
    """

    def __init__(self, aws_env_name: str, aws_env_component: str) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name (str): name of the env that failed
            aws_env_component (str): Name of the component that failed during up
        """

        super().__init__()

        self.msg = (
            f"Environment {aws_env_name} failed to up because {aws_env_component} "
            "is not reporting up after it should be running"
        )
        self.suggestion = (
            f"Please run `rib env aws down --name={aws_env_name} --force` and then "
            f"`rib env aws up --name={aws_env_name}` to reup the environment. If that "
            "doesn't work, please reach out to Two Six Labs with the issue."
        )


class RIB717(RIB000):
    """
    Purpose:
        RIB717 is for when starting an AWS env with Android enabled but the workers
        are not metal. instances need to be metal to allow for hardware acceleration
        which is necessary for android
    """

    def __init__(self):
        super().__init__()

        self.msg = (
            f"AWS environment workers must be metal instances with android client"
        )
        self.suggestion = (
            "Update the `--worker-instance-type` argument to be a metal instance type "
            "(e.g. c5.metal) and rerun the create command"
        )


class RIB718(RIB000):
    """
    Purpose:
        RIB718 is for creating/starting an aws env that has an ssh key name that is
        not found in AWS (will fail on up)
    """

    def __init__(self, ssh_key_name: str):
        """
        Purpose:
            Initialization of the exception.
        Args:
            ssh_key_name: name of the ssh key pair in aws
        """

        super().__init__()

        self.msg = f"The SSH Key {ssh_key_name} was not found in AWS"
        self.suggestion = (
            "Either add the SSH Key to the known key pairs in the AWS EC2 console or update "
            "the key name in the command and run again"
        )


class RIB719(RIB000):
    """
    Purpose:
        RIB719 is for incompatible instance types selected for an AWS env
    """

    def __init__(
        self, option: str, value: str, msg: str, suggestion: Optional[str] = None
    ):
        """
        Purpose:
            Initialization of the exception.
        Args:
            option: instance type option (e.g., --linux-node-instance-type)
            value: instance type value (e.g., t3.2xlarge)
            msg: error message
        """

        super().__init__()

        self.msg = f"Invalid instance type selected: {option}={value}: {msg}"
        if suggestion:
            self.suggestion = suggestion
        else:
            self.suggestion = "See https://aws.amazon.com/ec2/instance-types/ for descriptions of available instance types"


class RIB720(RIB000):
    """
    Purpose:
        RIB720 is for invalid/incompatible input parameters for an AWS env
    """

    def __init__(self, msg: str, suggestion: Optional[str] = None):
        """
        Purpose:
            Initialization of the exception.
        Args:
            msg: Error message
            suggestion: Suggestion message
        """

        super().__init__()

        self.msg = msg
        if suggestion:
            self.suggestion = suggestion


class RIB721(RIB000):
    """
    Purpose:
        RIB721 is for failure to determine AWS env resources/scheduling for nodes
    """

    def __init__(self, msg: str, suggestion: Optional[str] = None):
        """
        Purpose:
            Initialization of the exception.
        Args:
            msg: Error message
            suggestion: Suggestion message
        """

        super().__init__()

        self.msg = msg
        if suggestion:
            self.suggestion = suggestion


class RIB722(RIB000):
    """
    Purpose:
        RIB722 is for failure to read node instance topology JSON
    """

    def __init__(self, filename: str, error: str):
        """
        Purpose:
            Initialization of the exception
        Args:
            filename: Name of topology file being read
            error: Read/parse error that occurred
        """

        super().__init__()

        self.msg = f"Unable to read {filename}: {error}"
        self.suggestion = "Fix errors in the file, then retry the operation"


class RIB723(RIB000):
    """
    Purpose:
        RIB723 is for attempts to modify an AWS environment that is in use by a deployment
    """

    def __init__(self, aws_env_name: str, action: str):
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name: AWS environment name
            action: Attempted modification action
        """

        super().__init__()
        self.msg = (
            f"Unable to {action} {aws_env_name}, currently in use by a deployment"
        )
        self.suggestion = (
            f"Tear down the deployment or use the `--force` flag to {action} anyway"
        )


class RIB724(RIB000):
    """
    Purpose:
        RIB724 is for attempts to modify an AWS environment that is currently active
    """

    def __init__(self, aws_env_name: str, action: str):
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name: AWS environment name
            action: Attempted modification action
        """

        super().__init__()
        self.msg = f"Unable to {action} {aws_env_name}, currently active in AWS"
        self.suggestion = "Unprovision the environment to remove all AWS resources"


class RIB725(RIB000):
    """
    Purpose:
        RIB725 is for incompatible AWS env topology and deployment
    """

    def __init__(self, aws_env_name: str, topology_file: str):
        """
        Purpose:
            Initialization of the exception.
        Args:
            aws_env_name: AWS environment name
            toplogy_file: Location of topology JSON file
        """

        super().__init__()
        self.msg = f"AWS node topology from {topology_file} is not compatible with the AWS env {aws_env_name}"
        self.suggestion = "Ensure that the host AWS env has enough instances "


###
# Ansible Exceptions
###


class RIB800(RIB000):
    """
    Purpose:
        RIB800 is for failing to play a playbook
    """

    def __init__(
        self,
        playbook_filename: str,
        failed_task_count: int,
        failed_tasks: List[str],
        verbose: int = 0,
    ) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            playbook_filename: The name of the ansible playbook being run when this error occurred.
            failed_task_count: The number of failed tasks in the playbook.
            failed_tasks: A list of descriptions of each of the failed tasks.
            verbose: Flag to display full error text.
        """

        super().__init__()

        if verbose:
            max_characters = -1
        else:
            max_characters = 80

        parsed_failed_tasks = "...\n\t\t".join(
            [failed_task[:max_characters] for failed_task in failed_tasks]
        )
        self.msg = f"{playbook_filename} Ansible Playbook Failed"
        self.suggestion = (
            f"There were {failed_task_count} failures, These failures include: \n"
            f"\t\t{parsed_failed_tasks}..."
        )


class RIB801(RIB000):
    """
    Purpose:
        RIB801 is for playing a playbook timing out
    """

    def __init__(self, playbook_filename: str) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            playbook_filename (str): the playbook that timed out
        """

        super().__init__()

        self.msg = f"{playbook_filename} Ansible Playbook Timed Out"
        self.suggestion = "Please try again and increase the timeout"


class RIB802(RIB000):
    """
    Purpose:
        RIB802 is for when an ansible playbook is not found
    """

    def __init__(self, playbook_filename: str) -> None:
        """
        Purpose:
            Initialization of the exception.
        Args:
            playbook_filename (str): the playbook that isn't found
        """

        super().__init__()

        self.msg = f"Failed to load Ansible Playbook: {playbook_filename}"
        self.suggestion = "Please reach out to Two Six Labs"


###
# ADB Exceptions
###


class RIBa00(RIB000):
    """
    Purpose:
        RIBa00 is for incompatible host ADB version
    """

    def __init__(self, required_version: str):
        """
        Purpose:
            Initializes the exception.
        Args:
            required_version: Required ADB version
        """

        super().__init__()
        self.msg = "Host ADB is incompatible version"
        self.suggestion = f"Install ADB version {required_version} on the host"


class RIBa01(RIB000):
    """
    Purpose:
        RIBa01 is for connection errors communicating with the host ADB server
    """

    def __init__(self, error: Any):
        """
        Purpose:
            Initializes the exception.
        Args:
            error: Connection error
        """

        super().__init__()

        self.msg = f"Error communicating with host ADB server: {error}"
        self.suggestion = (
            "Restart RiB to re-configure the host ADB server. If the problem persists, "
            "email race@twosixtech.com"
        )


class RIBa02(RIB000):
    """
    Purpose:
        RIBa02 is for invalid Android device serial number
    """

    def __init__(self, serial: str, available: List[str]):
        """
        Purpose:
            Initializes the exception.
        Args:
            serial: Invalid serial number
            available: Available device serial numbers
        """

        super().__init__()

        self.msg = f"Invalid Android device serial number: {serial}"
        if available:
            self.suggestion = (
                "Use one of the following available Android devices:\n\t\t"
                + "\n\t\t".join(sorted(available))
            )
        else:
            self.suggestion = "No Android devices are available"


class RIBa03(RIB000):
    """
    Purpose:
        RIBa03 is for attempting to prepare an Android device that is not compatible with RACE
    """

    def __init__(self, serial: str, reason: str):
        """
        Purpose:
            Initializes the exception.
        Args:
            serial: Serial number of the device
        """

        super().__init__()

        self.msg = f"Device {serial} is not compatible with RACE: {reason}"
        self.suggestion = "Use an appropriate Android device"


class RIBa04(RIB000):
    """
    Purpose:
        RIBa04 is for attempting to prepare an Android device that has been already prepared
    """

    def __init__(
        self, deployment_name: str, rib_mode: str, serial: str, details: Dict[str, bool]
    ):
        """
        Purpose:
            Initializes the exception.
        Args:
            deployment_name: Deployment name
            rib_mode: Deployment type
            serial: Serial number of the device
            details: Dictionary of preparation status checks to their values
        """

        super().__init__()

        self.msg = f"Device has already been prepared for bridged node operations:"
        for detail_key in sorted(details.keys()):
            self.msg += f"\n\t\t{detail_key}: {details[detail_key]}"
        self.suggestion = (
            f"Run `rib deployment {rib_mode} bridged android unprepare --name={deployment_name} "
            f"--serial={serial}` then re-attempt to prepare the device."
        )


class RIBa05(RIB000):
    """
    Purpose:
        RIBa05 is for failure to prepare an Android device
    """

    def __init__(
        self, deployment_name: str, rib_mode: str, serial: str, details: Dict[str, bool]
    ):
        """
        Purpose:
            Initializes the exception.
        Args:
            deployment_name: Deployment name
            rib_mode: Deployment type
            serial: Serial number of the device
            details: Dictionary of preparation status checks to their values
        """

        super().__init__()

        self.msg = f"Failed to fully prepare the device for bridged node operations:"
        for detail_key in sorted(details.keys()):
            self.msg += f"\n\t\t{detail_key}: {details[detail_key]}"
        self.suggestion = (
            f"Run `rib deployment {rib_mode} bridged android unprepare --name={deployment_name} "
            f"--serial={serial}` then re-attempt to prepare the device."
        )


class RIBa06(RIB000):
    """
    Purpose:
        RIBa06 is for failure to unprepare an Android device
    """

    def __init__(
        self, deployment_name: str, rib_mode: str, serial: str, details: Dict[str, bool]
    ):
        """
        Purpose:
            Initializes the exception.
        Args:
            deployment_name: Deployment name
            rib_mode: Deployment type
            serial: Serial number of the device
            details: Dictionary of preparation status checks to their values
        """

        super().__init__()

        self.msg = f"Failed to unprepare the device"
        for detail_key in sorted(details.keys()):
            self.msg += f"\n\t\t{detail_key}: {details[detail_key]}"
        self.suggestion = (
            f"Run `rib deployment {rib_mode} bridged android unprepare --name={deployment_name} "
            f"--serial={serial}` to re-attempt to unprepare the device."
        )


class RIBa07(RIB000):
    """
    Purpose:
        RIBa07 is for attempting an operation an Android device that is not fully prepared
    """

    def __init__(
        self,
        action: str,
        deployment_name: str,
        rib_mode: str,
        serial: str,
        details: Dict[str, bool],
    ):
        """
        Purpose:
            Initializes the exception.
        Args:
            action: Attempted action
            deployment_name: Deployment name
            rib_mode: Deployment type
            serial: Serial number of the device
            details: Dictionary of preparation status checks to their values
        """

        super().__init__()

        self.msg = f"Unable to {action} device {serial}, device is not prepared for bridged operations"
        for detail_key in sorted(details.keys()):
            self.msg += f"\n\t\t{detail_key}: {details[detail_key]}"
        self.suggestion = (
            f"Run `rib deployment {rib_mode} bridged android prepare --name={deployment_name} "
            f"--serial={serial}` to prepare the device."
        )
