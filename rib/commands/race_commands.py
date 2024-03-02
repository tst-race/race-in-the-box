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
        RACE Command Group is responsible for information about RACE system (i.e.
        compatability)
"""

# Python Library Imports
import click

# Local Python Library Imports
# N/A


###
# Git Commands
###


@click.command("versions")
@click.pass_context
def versions(cli_context):
    """
    Get Versions of RACE compatible with this version of RiB
    """

    click.echo("RACE Compatible Versions:")

    for race_version in cli_context.obj.config.RACE_VERSIONS:
        click.echo(f"\t{race_version}")
