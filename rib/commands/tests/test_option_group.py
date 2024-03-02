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
    Tests for option_group.py
"""

# Python Library Imports
import click
from click.testing import CliRunner

# Local Python Library Imports
from rib.commands import option_group


def test_grouping_of_options():
    group1 = option_group.OptionGroup("grp1", name="Group of Options")
    group2 = option_group.OptionGroup(
        "other", name="Other Options", help="Explanation of options"
    )

    @click.command(cls=option_group.GroupedOptionCommand)
    @click.option("--abc", help="abc help")
    @group1.option("--foo", help="Foo help")
    @group1.option("--bar", help="Bar help")
    @group2.option("--baz", help="Baz help")
    @group2.option("--qux", help="Qux help")
    @click.option("--xyz", help="xyz help")
    def use_group_options(foo, bar, baz, qux, abc, xyz):
        click.echo(f"foo={foo} bar={bar}")
        click.echo(f"baz={baz} qux={qux}")
        click.echo(f"abc={abc} xyz={xyz}")

    runner = CliRunner()

    # With values
    result = runner.invoke(
        use_group_options,
        [
            "--foo=fizz",
            "--bar=buzz",
            "--baz=bizz",
            "--qux=fuzz",
            "--abc=def",
            "--xyz=uvw",
        ],
    )
    assert "foo=fizz bar=buzz" in result.output
    assert "baz=bizz qux=fuzz" in result.output
    assert "abc=def xyz=uvw" in result.output

    # Help text
    result = runner.invoke(use_group_options, ["--help"])
    assert "Options:" in result.output
    assert "abc help" in result.output
    assert "xyz help" in result.output
    assert "Group of Options:" in result.output
    assert "Foo help" in result.output
    assert "Bar help" in result.output
    assert "Other Options:" in result.output
    assert "Explanation of options" in result.output
    assert "Baz help" in result.output
    assert "Qux help" in result.output


def test_mutually_exclusive_option_groups():
    filter_set = option_group.MutuallyExclusiveOptions()
    by_name = filter_set.group("by_name", name="Name Filter Options")
    by_age = filter_set.group("by_age", name="Age Filter Options")

    @click.command(cls=option_group.GroupedOptionCommand)
    @by_name.option("--startswith")
    @by_name.option("--endswith")
    @by_age.option("--above", type=int)
    @by_age.option("--below", type=int)
    @filter_set.result("filter_type")
    def use_filter_options(startswith, endswith, above, below, filter_type):
        click.echo(f"filter_type={filter_type}")
        if filter_type == "by_name":
            click.echo(f"startswith={startswith} endswith={endswith}")
        if filter_type == "by_age":
            click.echo(f"above={above} below={below}")

    runner = CliRunner()

    # No options
    result = runner.invoke(use_filter_options, [])
    assert "filter_type=None" in result.output
    assert "startswith" not in result.output
    assert "above" not in result.output

    # Group 1 options
    result = runner.invoke(use_filter_options, ["--startswith=abc"])
    assert "filter_type=by_name" in result.output
    assert "startswith=abc endswith=None" in result.output
    assert "above" not in result.output

    result = runner.invoke(use_filter_options, ["--startswith=abc", "--endswith=xyz"])
    assert "filter_type=by_name" in result.output
    assert "startswith=abc endswith=xyz" in result.output
    assert "above" not in result.output

    # Group 2 options
    result = runner.invoke(use_filter_options, ["--below=65"])
    assert "filter_type=by_age" in result.output
    assert "startswith" not in result.output
    assert "above=None below=65" in result.output

    # Mixed options
    result = runner.invoke(use_filter_options, ["--endswith=xyz", "--above=18"])
    assert result.exit_code != 0
    assert "Cannot combine Name Filter Options with Age Filter Options" in result.output


def test_mutually_exclusive_option_groups_with_defaults():
    filter_set = option_group.MutuallyExclusiveOptions()
    by_name = filter_set.group("by_name", name="Name Filter Options")
    by_age = filter_set.group("by_age", name="Age Filter Options")

    @click.command(cls=option_group.GroupedOptionCommand)
    @by_name.option("--startswith")
    @by_name.option("--endswith", default="-suffix")
    @by_age.option("--above", default=21, type=int)
    @by_age.option("--below", type=int)
    @filter_set.result("filter_type")
    def use_filter_options(startswith, endswith, above, below, filter_type):
        click.echo(f"filter_type={filter_type}")
        click.echo(f"startswith={startswith} endswith={endswith}")
        click.echo(f"above={above} below={below}")

    runner = CliRunner()

    # No options
    result = runner.invoke(use_filter_options, [])
    assert "filter_type=None" in result.output
    assert "startswith=None endswith=-suffix" in result.output
    assert "above=21 below=None" in result.output

    # Group 1 options
    result = runner.invoke(use_filter_options, ["--startswith=abc"])
    assert "filter_type=by_name" in result.output
    assert "startswith=abc endswith=-suffix" in result.output
    assert "above=21 below=None" in result.output

    # Group 2 options
    result = runner.invoke(use_filter_options, ["--below=65"])
    assert "filter_type=by_age" in result.output
    assert "startswith=None endswith=-suffix" in result.output
    assert "above=21 below=65" in result.output


def test_mutually_exclusive_option_groups_with_default_group():
    filter_set = option_group.MutuallyExclusiveOptions()
    by_name = filter_set.group("by_name", name="Name Filter Options")
    by_age = filter_set.group("by_age", name="Age Filter Options")

    @click.command(cls=option_group.GroupedOptionCommand)
    @by_name.option("--startswith", default="prefix-")
    @by_name.option("--endswith", default="-suffix")
    @by_age.option("--above", default=21, type=int)
    @by_age.option("--below", default=70, type=int)
    @filter_set.result("--filter-type", default=by_name.key)
    def use_filter_options(startswith, endswith, above, below, filter_type):
        click.echo(f"filter_type={filter_type}")
        click.echo(f"startswith={startswith} endswith={endswith}")
        click.echo(f"above={above} below={below}")

    runner = CliRunner()

    # No options
    result = runner.invoke(use_filter_options, [])
    assert "filter_type=by_name" in result.output
    assert "startswith=prefix- endswith=-suffix" in result.output
    assert "above=21 below=70" in result.output

    # Group 1 options
    result = runner.invoke(use_filter_options, ["--startswith=abc"])
    assert "filter_type=by_name" in result.output
    assert "startswith=abc endswith=-suffix" in result.output
    assert "above=21 below=70" in result.output

    # Group 2 options
    result = runner.invoke(use_filter_options, ["--below=65"])
    assert "filter_type=by_age" in result.output
    assert "startswith=prefix- endswith=-suffix" in result.output
    assert "above=21 below=65" in result.output


def test_mutually_exclusive_option_groups_with_user_value():
    filter_set = option_group.MutuallyExclusiveOptions()
    by_name = filter_set.group("by_name", name="Name Filter Options")
    by_age = filter_set.group("by_age", name="Age Filter Options")

    @click.command(cls=option_group.GroupedOptionCommand)
    @by_name.option("--startswith", default="prefix-")
    @by_name.option("--endswith", default="-suffix")
    @by_age.option("--above", default=21, type=int)
    @by_age.option("--below", default=70, type=int)
    @filter_set.result("--filter-type", allow_user_value=True)
    def use_filter_options(startswith, endswith, above, below, filter_type):
        click.echo(f"filter_type={filter_type}")
        click.echo(f"startswith={startswith} endswith={endswith}")
        click.echo(f"above={above} below={below}")

    runner = CliRunner()

    # No options
    result = runner.invoke(use_filter_options, [])
    assert "filter_type=None" in result.output
    assert "startswith=prefix- endswith=-suffix" in result.output
    assert "above=21 below=70" in result.output

    # Direct override
    result = runner.invoke(use_filter_options, ["--filter-type=by_age"])
    assert "filter_type=by_age" in result.output
    assert "startswith=prefix- endswith=-suffix" in result.output
    assert "above=21 below=70" in result.output


def test_required_mutually_exclusive_option_group():
    filter_set = option_group.MutuallyExclusiveOptions()
    by_name = filter_set.group("by_name", name="Name Filter Options")
    by_age = filter_set.group("by_age", name="Age Filter Options")

    @click.command(cls=option_group.GroupedOptionCommand)
    @by_name.option("--name")
    @by_age.option("--age", type=int)
    @filter_set.result("filter_type", expose_value=False, required=True)
    def use_filter_options(name, age):
        click.echo(f"name={name} age={age}")

    runner = CliRunner()

    # No options
    result = runner.invoke(use_filter_options, [])
    assert result.exit_code != 0
    assert "Error: Missing" in result.output

    # With option
    result = runner.invoke(use_filter_options, ["--name=John"])
    assert result.exit_code == 0


def test_multiple_mutually_exclusive_option_groups():
    filter_set = option_group.MutuallyExclusiveOptions()
    filter_by_name = filter_set.group("by_name")
    filter_by_age = filter_set.group("by_age", name="Age Filter Options")

    sort_set = option_group.MutuallyExclusiveOptions()
    sort_by_name = sort_set.group("by_name", name="Name Sort Options")
    sort_by_age = sort_set.group("by_age")

    @click.command(cls=option_group.GroupedOptionCommand)
    @filter_by_name.option("--name")
    @filter_by_age.option("--age", type=int)
    @sort_by_name.option("--sort-by-name", flag_value=True)
    @sort_by_age.option("--sort-by-age", flag_value=True)
    @filter_set.result("filter_type", expose_value=False)
    @sort_set.result("sort_type", expose_value=False)
    def use_filter_and_sort(name, age, sort_by_name, sort_by_age):
        click.echo(f"name={name} age={age}")
        if sort_by_name:
            click.echo("sorted by name")
        if sort_by_age:
            click.echo("sorted by age")

    runner = CliRunner()

    # No options
    result = runner.invoke(use_filter_and_sort, [])
    assert "name=None age=None" in result.output
    assert "sorted by" not in result.output

    # Just filter options
    result = runner.invoke(use_filter_and_sort, ["--name=John"])
    assert "name=John age=None" in result.output
    assert "sorted by" not in result.output

    result = runner.invoke(use_filter_and_sort, ["--age=25"])
    assert "name=None age=25" in result.output
    assert "sorted by" not in result.output

    # Just sort options
    result = runner.invoke(use_filter_and_sort, ["--sort-by-age"])
    assert "name=None age=None" in result.output
    assert "sorted by name" not in result.output
    assert "sorted by age" in result.output

    result = runner.invoke(use_filter_and_sort, ["--sort-by-name"])
    assert "name=None age=None" in result.output
    assert "sorted by name" in result.output
    assert "sorted by age" not in result.output

    # Filter and sort
    result = runner.invoke(use_filter_and_sort, ["--age=25", "--sort-by-name"])
    assert "name=None age=25" in result.output
    assert "sorted by name" in result.output
    assert "sorted by age" not in result.output

    # Violation of filter exclusivity
    result = runner.invoke(use_filter_and_sort, ["--name=John", "--age=25"])
    assert result.exit_code != 0
    assert "Cannot combine by_name Options with Age Filter Options" in result.output

    # Violation of sort exclusivity
    result = runner.invoke(use_filter_and_sort, ["--sort-by-name", "--sort-by-age"])
    assert result.exit_code != 0
    assert "Cannot combine Name Sort Options with by_age Options" in result.output
