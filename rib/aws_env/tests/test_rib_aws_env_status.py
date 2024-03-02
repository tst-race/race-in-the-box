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
    Test file for rib_aws_env_status.py
"""

# Python Library Imports
import pytest

# Local Python Library Imports
from rib.aws_env.rib_aws_env_status import (
    AwsComponentStatus,
    StatusReport,
    convert_cf_status_to_enum,
    convert_ec2_status_to_enum,
    convert_efs_status_to_enum,
    create_parent_report,
    get_parent_status,
)


###
# convert_cf_status_to_enum
###


@pytest.mark.parametrize(
    "cf_status,expected_status",
    [
        ("CREATE_COMPLETE", AwsComponentStatus.READY),
        ("CREATE_IN_PROGRESS", AwsComponentStatus.NOT_READY),
        ("CREATE_FAILED", AwsComponentStatus.ERROR),
        ("DELETE_COMPLETE", AwsComponentStatus.NOT_PRESENT),
        ("DELETE_FAILED", AwsComponentStatus.ERROR),
        ("DELETE_IN_PROGRESS", AwsComponentStatus.NOT_READY),
        # We don't initiate any rollback, update, or import actions so they're all UNKOWN
        ("ROLLBACK_IN_PROGRESS", AwsComponentStatus.UNKNOWN),
        ("UPDATE_IN_PROGRESS", AwsComponentStatus.UNKNOWN),
        ("IMPORT_IN_PROGRESS", AwsComponentStatus.UNKNOWN),
    ],
)
def test_convert_cf_status_to_enum(cf_status, expected_status):
    """Verify convert_cf_status_to_enum for given CloudFormation status values"""
    assert expected_status == convert_cf_status_to_enum(cf_status)


###
# convert_ec2_status_to_enum
###


@pytest.mark.parametrize(
    "ec2_status,expected_status",
    [
        ("pending", AwsComponentStatus.NOT_READY),
        ("running", AwsComponentStatus.READY),
        ("shutting-down", AwsComponentStatus.NOT_READY),
        ("terminated", AwsComponentStatus.NOT_PRESENT),
        ("stopping", AwsComponentStatus.NOT_READY),
        ("stopped", AwsComponentStatus.NOT_PRESENT),
        ("unrecognized", AwsComponentStatus.UNKNOWN),
    ],
)
def test_convert_ec2_status_to_enum(ec2_status, expected_status):
    """Verify convert_ec2_status_to_enum for given EC2 status values"""
    assert expected_status == convert_ec2_status_to_enum(ec2_status)


###
# convert_efs_status_to_enum
###


@pytest.mark.parametrize(
    "efs_status,expected_status",
    [
        ("available", AwsComponentStatus.READY),
        ("creating", AwsComponentStatus.NOT_READY),
        ("deleting", AwsComponentStatus.NOT_READY),
        ("deleted", AwsComponentStatus.NOT_PRESENT),
        ("error", AwsComponentStatus.ERROR),
        ("updating", AwsComponentStatus.UNKNOWN),
    ],
)
def test_convert_efs_status_to_enum(efs_status, expected_status):
    """Verify convert_efs_status_to_enum for given EFS status values"""
    assert expected_status == convert_efs_status_to_enum(efs_status)


###
# create_parent_report
###


def test_create_parent_report_sets_overall_parent_status():
    """
    Verify create_parent_report uses get_parent_status to set the overall parent status from the
    status of all children status reports
    """
    parent_report = create_parent_report(
        {
            "one": StatusReport(status=AwsComponentStatus.READY),
            "two": StatusReport(status=AwsComponentStatus.NOT_READY),
        }
    )
    assert parent_report == StatusReport(
        status=AwsComponentStatus.NOT_READY,
        children={
            "one": StatusReport(status=AwsComponentStatus.READY),
            "two": StatusReport(status=AwsComponentStatus.NOT_READY),
        },
        reason=None,
    )


###
# get_parent_status
###


@pytest.mark.parametrize(
    "status", [(status) for status in AwsComponentStatus._member_names_]
)
def test_get_parent_status_all_same(status):
    """Verify get_parent_status assigns same status as all-same children status"""
    assert status == get_parent_status([status, status, status])


@pytest.mark.parametrize(
    "status", [(status) for status in AwsComponentStatus._member_names_]
)
def test_get_parent_status_when_error(status):
    """Verify get_parent_status assigns error status when at least one child is in error"""
    assert AwsComponentStatus.ERROR == get_parent_status(
        [status, AwsComponentStatus.ERROR]
    )


@pytest.mark.parametrize(
    "children",
    [
        ([AwsComponentStatus.NOT_READY, AwsComponentStatus.UNKNOWN]),
        ([AwsComponentStatus.NOT_READY, AwsComponentStatus.NOT_PRESENT]),
        ([AwsComponentStatus.NOT_READY, AwsComponentStatus.NOT_READY]),
        ([AwsComponentStatus.NOT_READY, AwsComponentStatus.READY]),
        # ([AwsComponentStatus.NOT_READY, AwsComponentStatus.ERROR]), -- would be error
        ([AwsComponentStatus.READY, AwsComponentStatus.UNKNOWN]),
        ([AwsComponentStatus.READY, AwsComponentStatus.NOT_PRESENT]),
        ([AwsComponentStatus.READY, AwsComponentStatus.NOT_READY]),
        ([AwsComponentStatus.READY, AwsComponentStatus.NOT_READY]),
        # ([AwsComponentStatus.READY, AwsComponentStatus.READY]), -- would be ready
        # ([AwsComponentStatus.READY, AwsComponentStatus.ERROR]), -- would be error
    ],
)
def test_get_parent_status_when_not_ready(children):
    """
    Verify get_parent_status assigns not-ready status when at least one child is ready or not-ready
    """
    assert AwsComponentStatus.NOT_READY == get_parent_status(children)


def test_get_parent_status_when_unknown():
    """Verify get_parent_status assigns unknown with only not-present and unknown child statuses"""
    assert AwsComponentStatus.UNKNOWN != get_parent_status(
        [
            AwsComponentStatus.UNKNOWN,
            AwsComponentStatus.NOT_PRESENT,
            AwsComponentStatus.READY,
        ]
    )
    assert AwsComponentStatus.UNKNOWN == get_parent_status(
        [
            AwsComponentStatus.UNKNOWN,
            AwsComponentStatus.NOT_PRESENT,
        ]
    )
