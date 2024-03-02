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

"""
    Purpose:
        Test File for threading_utils.py
"""

# Python Library Imports
import concurrent.futures
import os
import sys
import pytest
import time
from unittest import mock

# Local Library Imports
from rib.utils import threading_utils, error_utils


###
# Fixtures
###


# None at the Moment


###
# Mocked Functions
###


def func_return_value(x, y="test"):
    """
    Purpose:
        A function with an arg and kwarg
    Args:
        x (int): test value
        y (str): test value
    """

    return f"{x} - {y}"


class RIB_TEST_ERROR(error_utils.RIB000):
    def __init__(self):
        super().__init__()


def func_exception():
    """
    Purpose:
        A function that will throw an exception
    Args:
        N/A
    """

    raise RIB_TEST_ERROR


def func_return_value_with_delay(x, y="test"):
    """
    Purpose:
        A function with an arg and kwarg with a delay
    Args:
        x (int): test value
        y (str): test value
    """

    time.sleep(2)
    return f"{x} - {y}"


###
# Test threading_utils functions
###


######
# create_thread_executor
######


def test_create_thread_executor():
    """
    Purpose:
        Test Threading Utils can create an executor
    Args:
        N/A
    """

    thread_executor = threading_utils.create_thread_executor()

    assert type(thread_executor) == concurrent.futures.thread.ThreadPoolExecutor


######
# shutdown_thread_executor
######


def test_shutdown_thread_executor():
    """
    Purpose:
        Test Threading Utils can shutdown an executor
    Args:
        N/A
    """

    thread_executor = threading_utils.create_thread_executor()

    threading_utils.shutdown_thread_executor(thread_executor)


######
# get_threaded_function_results_as_completed
######


def test_get_threaded_function_results_as_completed_good():
    """
    Purpose:
        Test Threading Utils get_threaded_function_results_as_completed
        will properly return the results of threaded functions as they
        are completed.

        Will test functions that do not throw exceptions
    Args:
        N/A
    """

    thread_executor = threading_utils.create_thread_executor()

    thread_function_futures = {}
    for idx in range(10):
        thread_function_futures[idx] = threading_utils.execute_function_in_thread(
            thread_executor, func_return_value, args=[idx], kwargs={"y": idx}
        )

    threaded_function_results = (
        threading_utils.get_threaded_function_results_as_completed(
            thread_function_futures
        )
    )

    assert len(threaded_function_results["return_values"]) == 10
    assert len(threaded_function_results["exceptions"]) == 0


def test_get_threaded_function_results_as_completed_exceptions():
    """
    Purpose:
        Test Threading Utils get_threaded_function_results_as_completed
        will properly return the results of threaded functions as they
        are completed.

        Will test functions that throw exceptions
    Args:
        N/A
    """

    thread_executor = threading_utils.create_thread_executor()

    thread_function_futures = {}
    for idx in range(10):
        thread_function_futures[idx] = threading_utils.execute_function_in_thread(
            thread_executor, func_exception
        )

    threaded_function_results = (
        threading_utils.get_threaded_function_results_as_completed(
            thread_function_futures
        )
    )

    assert len(threaded_function_results["return_values"]) == 0
    assert len(threaded_function_results["exceptions"]) == 10

    for job_name, raised_exception in threaded_function_results["exceptions"].items():
        assert type(raised_exception) is RIB_TEST_ERROR


######
# get_threaded_function_result
######


def test_get_threaded_function_result_good():
    """
    Purpose:
        Test Threading Utils can return the results of a threaded function that
        was successfully completed
    Args:
        N/A
    """

    thread_executor = threading_utils.create_thread_executor()

    thread_function_future = threading_utils.execute_function_in_thread(
        thread_executor, func_return_value, args=[1], kwargs={"y": 1}
    )

    threaded_function_result = threading_utils.get_threaded_function_result(
        thread_function_future
    )

    assert threaded_function_result == "1 - 1"


def test_get_threaded_function_result_exceptions():
    """
    Purpose:
        Test Threading Utils can return the results of a threaded function that
        threw an exception
    Args:
        N/A
    """

    thread_executor = threading_utils.create_thread_executor()

    thread_function_future = threading_utils.execute_function_in_thread(
        thread_executor, func_exception
    )

    with pytest.raises(RIB_TEST_ERROR):
        threaded_function_result = threading_utils.get_threaded_function_result(
            thread_function_future
        )


def test_get_threaded_function_result_incomplete():
    """
    Purpose:
        Test Threading Utils will not return the results of a threaded function that
        is not completed
    Args:
        N/A
    """

    thread_executor = threading_utils.create_thread_executor()

    thread_function_future = threading_utils.execute_function_in_thread(
        thread_executor, func_return_value_with_delay, args=[1], kwargs={"y": 1}
    )

    with pytest.raises(threading_utils.ThreadedFunctionNotComplete):
        threaded_function_result = threading_utils.get_threaded_function_result(
            thread_function_future
        )
