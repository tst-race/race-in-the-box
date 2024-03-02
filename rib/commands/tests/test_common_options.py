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
    Tests for common_options.py
"""

# Python Library Imports
from enum import Enum
import click
from click.testing import CliRunner

# Local Python Library Imports
from rib.commands import common_options


def test_race_version_option():
    @click.command()
    @common_options.race_version_option()
    def use_race_version(race_version: str) -> None:
        click.echo(f"race_version={race_version}")

    @click.command()
    @common_options.race_version_option(command_help="Which RACE version to use")
    def use_custom_help(race_version: str) -> None:
        pass

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(use_race_version, [])
    assert f"race_version={common_options.DEFAULT_RACE_VERSION}" in result.output

    # When value is specified
    result = runner.invoke(use_race_version, ["--race=3.1.4"])
    assert "race_version=3.1.4" in result.output

    # Default help text
    result = runner.invoke(use_race_version, ["--help"])
    assert "What version of RACE" in result.output

    # Custom help text
    result = runner.invoke(use_custom_help, ["--help"])
    assert "Which RACE version to use" in result.output


def test_cache_option():
    @click.command()
    @common_options.cache_option()
    def use_cache(cache) -> None:
        if isinstance(cache, Enum):
            click.echo(f"cache = {cache}")

    runner = CliRunner()

    # When no value specified
    result = runner.invoke(use_cache, [])
    assert "cache = auto" in result.output

    # When lowercase value specified
    result = runner.invoke(use_cache, ["--cache=always"])
    assert "cache = always" in result.output

    # When uppercase value specified
    result = runner.invoke(use_cache, ["--cache=NEVER"])
    assert "cache = never" in result.output
