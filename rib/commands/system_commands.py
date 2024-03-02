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
        System Command Group is responsible for verifying and configuring the user's
        system.
"""

# Python Library Imports
import click

# Local Python Library Imports
from rib.commands.common_options import rib_mode_option
from rib.utils import system_utils


###
# System Commands
###


@click.command("verify")
@rib_mode_option()
@click.pass_context
def verify(cli_context, rib_mode):
    """
    Verify a user's system is capable of running race in the box
    """
    click.echo(f"Verify System ({rib_mode} mode)")
    system_requirements = cli_context.obj.config.SYSTEM_REQUIREMENTS.get(rib_mode, None)
    system_utils.verify_system_requirements(system_requirements)
