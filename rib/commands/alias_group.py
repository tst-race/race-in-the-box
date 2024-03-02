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
    Custom command group to support aliases
"""

# Python Library Imports
import click
from typing import Callable, List, Optional


class AliasGroup(click.Group):
    """
    Purpose:
        Custom command group to support aliases
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Purpose:
            Initializes the group
        Args:
            args: Positional arguments
            kwargs: Keyword arguments
        Returns:
            N/A
        """
        super().__init__(*args, **kwargs)
        self.aliases = {}

    def command(self, *args, **kwargs) -> Callable:
        """
        Purpose:
            Returns a custom decorator to save the specified aliases for the
            decorated command function.
        Args:
            args: Positional arguments
            kwargs: Keyword arguments
        """

        def decorator(func):
            cmd = super().command(*args, **kwargs)(func)
            aliases = kwargs.pop("aliases", None)
            if aliases:
                for alias in aliases:
                    self.aliases[alias] = cmd.name
            return cmd

        return decorator

    def add_command(
        self,
        command: click.Command,
        name: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> None:
        super().add_command(command, name)
        if aliases:
            if not name:
                name = command.name
            for alias in aliases:
                self.aliases[alias] = name

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command:
        """
        Purpose:
            Lookup the command of the given name, using aliases if an exact match is not
            found.
        Args:
            ctx: Click command context
            cmd_name: Command name
        Returns:
            Command, or None if no match is found
        """
        cmd = super().get_command(ctx, cmd_name)
        if cmd:
            return cmd

        alias = self.aliases.get(cmd_name, None)
        if alias:
            cmd = super().get_command(ctx, alias)

        return cmd
