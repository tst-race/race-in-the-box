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
    Click extensions to support groupings of options
Example:
    mut_options = MutuallyExclusiveOptions()
    mut_group_1 = mut_options.group("group_1", help="Options for Group 1")
    mut_group_2 = mut_options.group("group_2", help="Options for Group 2")
    group_3 = OptionGroup("advanced", help="Advanced Options")

    @click.command("foo", cls=GroupedOptionCommand)
    @click.option("--bar")
    @mut_group_1.option("--fizz")
    @mut_group_1.option("--buzz")
    @mut_group_2.option("--baz")
    @mut_options.result("chosen_option_type")
    @group_3.option("--qux")
    @group_3.option("--quux")
    @click.option("--verbose")
    def foo(bar, fizz, buzz, baz, chosen_option_type, qux, quux, verbose):
        pass
"""

# Python Library Imports
import click
from typing import Any, Callable, List, Mapping, Optional, Tuple


class _OptionInGroup(click.Option):
    """
    Purpose:
        Customized option that is part of an option group
    """

    def __init__(self, *args, **kwargs):
        """
        Purpose:
            Initializes the option
        Args:
            args: Positional arguments
            kwargs: Keyword arguments
        Returns:
            N/A
        """
        self.group = kwargs.pop("group")
        super().__init__(*args, **kwargs)


class GroupedOptionCommand(click.Command):
    """
    Purpose:
        Customized command to print options sorted by group in help output
    Example:
        @click.command("foo", cls=GroupedOptionCommand)
    """

    def format_options(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """
        Purpose:
            Writes all options into the formatter, organized by group
        Args:
            ctx: Click context
            formatter: Click help formatter
        Returns:
            N/A
        """
        ungrouped_opts = []
        groups = {}
        for param in self.get_params(ctx):
            rv = param.get_help_record(ctx)
            if rv is not None:
                if isinstance(param, _OptionInGroup):
                    groups.setdefault(param.group, [])
                    groups[param.group].append(rv)
                else:
                    ungrouped_opts.append(rv)

        if ungrouped_opts:
            with formatter.section("Options"):
                formatter.write_dl(ungrouped_opts)

        for group in groups:
            with formatter.section(group.name):
                if group.help:
                    with formatter.indentation():
                        formatter.write_paragraph()
                        formatter.write_text(group.help)
                        formatter.write_paragraph()
                formatter.write_dl(groups[group])


class OptionGroup:
    """
    Purpose:
        Parent scope for a grouping of related options
    Example:
        advanced_opts = OptionGroup("advanced", name="Advanced Options")
        @advanced_opts.option("--advanced-option")
    """

    # pylint: disable=redefined-builtin
    def __init__(
        self, key: str, name: Optional[str] = None, help: Optional[str] = None
    ) -> None:
        """
        Purpose:
            Initializes the option group
        Args:
            key: Unique identifier of the group
            name: Name of the group (used for messages)
            help: Help text for the group
        Returns:
            N/A
        """
        self.key = key
        self.name = name or f"{key} Options"
        self.help = help

    def option(self, *args, **kwargs):
        """
        Purpose:
            Defines an option in the group
        Args:
            args: Positional arguments
            kwargs: Keyword arguments
        """
        kwargs["cls"] = _OptionInGroup
        kwargs["group"] = self
        return click.option(*args, **kwargs)


class _MutualExclusionGroupOption(click.Option):
    """
    Purpose:
        Customized option to hold the resulting group name from a set of
        mutually-exclusive option groups
    """

    def __init__(
        self,
        *args,
        parent: "MutuallyExclusiveOptions",
        allow_user_value: bool,
        **kwargs,
    ):
        """
        Purpose:
            Initializes the option
        Args:
            args: Positional arguments
            parent: Parent options scope
            allow_user_value: Allow the user to set the mutual-exclusion group to be selected via an option flag
            kwargs: Keyword arguments
        Returns:
            N/A
        """
        self.parent = parent
        self.allow_user_value = allow_user_value
        super().__init__(*args, **kwargs)

    def handle_parse_result(
        self, ctx: click.Context, opts: Mapping[str, Any], args: List[str]
    ) -> Tuple[Any, List[str]]:
        """
        Purpose:
            Determines which mutually-exclusive group was used based on the current
            set of options being parsed.

            If options are given for multiple mutually-exclusive groups, then a UsageError
            is raised.
        Args:
            ctx: Click context
            opts: Current options being parsed
            args: Current arguments being parsed
        Return:
            Resulting mutually-exclusive group name, or None if no options chosen
        """
        mut_exclusive_group = None
        for param in ctx.command.params:
            if isinstance(param, _OptionInGroup):
                # Specifically checking for identity, not equality, to ensure the
                # group is part of this mutual-exclusion set
                if param.group is self.parent.groups.get(param.group.key, None):
                    if param.name in opts:
                        if mut_exclusive_group is None:
                            mut_exclusive_group = param.group.key
                        elif mut_exclusive_group == param.group.key:
                            pass
                        else:
                            raise click.UsageError(
                                ctx=ctx,
                                message=(
                                    f"Cannot combine {self.parent.groups.get(mut_exclusive_group).name}"
                                    f" with {param.group.name}"
                                ),
                            )

        if not mut_exclusive_group and self.allow_user_value:
            mut_exclusive_group, _ = self.consume_value(ctx, opts)

        if not mut_exclusive_group and self.default:
            mut_exclusive_group = self.default

        if not mut_exclusive_group and self.required:
            message = "Must provide some or all options from one of the following option groups:"
            for group in self.parent.groups.values():
                message += f"\n\t{group.name}"
            raise click.MissingParameter(
                ctx=ctx,
                param_type="option",
                message=message,
            )

        if self.expose_value:
            ctx.params[self.name] = mut_exclusive_group

        return mut_exclusive_group, args


class MutuallyExclusiveOptions:
    """
    Purpose:
        Parent scope for a set of mutually-exclusive option groups
    Example:
        opt_groups = MutuallyExclusiveOptions()
        group_1 = opt_groups.group("group_1")
        group_2 = opt_groups.group("group_2")

        @click.command(cls=GroupedOptionCommand)
        @group_1.option("--group-1-opt")
        @group_2.option("--group-2-opt")
        @opt_groups.result("--use-group")
    """

    def __init__(self) -> None:
        """
        Purpose:
            Initializes the mutually-exclusive option group
        Args:
            N/A
        Returns:
            N/A
        """
        self.groups = {}

    # pylint: disable=redefined-builtin
    def group(
        self, key: str, name: Optional[str] = None, help: Optional[str] = None
    ) -> OptionGroup:
        """
        Purpose:
            Defines a mutual-exclusion option group
        Args:
            key: Unique identifier of the group
            name: Name of the group
            help: Help text for the group
        """
        group = OptionGroup(key, name=name, help=help)
        self.groups[key] = group
        return group

    def result(
        self,
        name: str,
        allow_user_value: bool = False,
        default: str = None,
        expose_value: bool = True,
        required: bool = False,
    ) -> Callable[[click.decorators.FC], click.decorators.FC]:
        """
        Purpose:
            Defines a pseudo-option for the name of the selected mutual-exclusion group
        Args:
            name: Name of the option into which to place the selected group name
            allow_user_value: Allow user to specify value as option
            default: Default selected group (assumes group options have defaults)
            expose_value: Whether to expose the value as an argument
            required: Whether a mutually-exclusive option group must be selected
        """
        if not name.startswith("--"):
            name = f"--{name}"
        return click.option(
            name,
            allow_user_value=allow_user_value,
            cls=_MutualExclusionGroupOption,
            default=default,
            expose_value=expose_value,
            hidden=True,
            parent=self,
            required=required,
            type=click.UNPROCESSED,
        )
