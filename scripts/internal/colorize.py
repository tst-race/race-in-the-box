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

# -----------------------------------------------------------------------------
# Script to colorize RACE log files
#
# Example:
#     colorize.py --by=thread race.log
# -----------------------------------------------------------------------------

import click
import random
import re
import sys
from typing import IO


###
# Colors
###

ansi_colors = [
    "blue",
    "red",
    "green",
    "yellow",
    "cyan",
    "magenta",
    "bright_blue",
    "bright_red",
    "bright_green",
    "bright_yellow",
    "bright_cyan",
    "bright_magenta",
]


def get_next_color() -> str:
    """
    Obtains the next available ANSI color, or a randomly generated one if
    we've exhausted all pre-defined colors
    """
    try:
        return ansi_colors.pop()
    except IndexError:
        return (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))


###
# Colorize by log level
###


level_re = re.compile(r"^[0-9\-]+ [0-9:\.]+: ([A-Z]+): .*")
colors_by_level = {
    "DEBUG": "blue",
    "WARNING": "yellow",
    "ERROR": "red",
}


def colorize_by_level(message: str) -> str:
    """Style the given log message line according to the log level of the message"""
    match = level_re.match(message)
    if match:
        return click.style(message, fg=colors_by_level.get(match.group(1)))
    return message


###
# Colorize by thread
###

thread_re = re.compile(r".*\(thread=([a-f0-9]+)\).*")
colors_by_thread_id = {}


def colorize_by_thread(message: str) -> str:
    """Style the given log message line according to the associated thread ID of the message"""
    match = thread_re.match(message)
    if match:
        thread_id = match.group(1)
        if thread_id not in colors_by_thread_id:
            colors_by_thread_id[thread_id] = get_next_color()
        return click.style(message, fg=colors_by_thread_id[thread_id])
    return message


###
# Colorize by module
###

module_re = re.compile(r".*[A-Z]+: ([a-zA-Z0-9_]+):.*")
colors_by_module_name = {}


def colorize_by_module(message: str) -> str:
    """Style the given log message line according to the plugin/module that logged the message"""
    match = module_re.match(message)
    if match:
        module_name = match.group(1)
        if module_name not in colors_by_module_name:
            colors_by_module_name[module_name] = get_next_color()
        return click.style(message, fg=colors_by_module_name[module_name])
    return message


styles = {
    "level": colorize_by_level,
    "thread": colorize_by_thread,
    "module": colorize_by_module,
}


@click.command()
@click.argument("log-file", default=sys.stdin, type=click.File("r"))
@click.option(
    "--by",
    default="level",
    help="Colorize based on the log message parameter",
    type=click.Choice(["level", "thread", "module"]),
)
def colorize(log_file: IO, by: str):
    """
    Style each line of the log file using either the log level, thread ID, or plugin/module name
    """
    style = styles[by]
    for line in log_file:
        click.echo(style(line), color=True, nl=False)


if __name__ == "__main__":
    colorize()
