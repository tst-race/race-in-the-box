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
        RiB Utilities for using python threading
"""

# Python Library Imports
import concurrent.futures

# Local Library Imports
from rib.utils import error_utils


###
# Custom Exceptions
###


class ThreadedFunctionNotComplete(Exception):
    """
    Purpose:
        ThreadNotComplete is a custom exception raised when calling
        to get results from a non-complete thread
    """

    pass


###
# Executor Functions
###


def create_thread_executor(max_workers=None):
    """
    Purpose:
        Create a Thread Pool
    Args:
        max_workers (Int): Num Workers
    Return:
        thread_executor (ThreadPoolExecutor Obj): Thread pool executor
    """

    if max_workers:
        return concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="",  # TODO, would like to get name from threads
            # initializer=None,
            # initargs=()
        )
    else:
        return concurrent.futures.ThreadPoolExecutor(
            thread_name_prefix="",
            # initializer=None,
            # initargs=()
        )


def shutdown_thread_executor(thread_executor, wait=True):
    """
    Purpose:
        Shutdown an active Thread Pool
    Args:
        wait (Bool): Wait for shutdown?
    Return:
        N/A
    """

    thread_executor.shutdown(wait=wait)


###
# Submit Functions
###


def execute_function_in_thread(
    thread_executor, threaded_function, args=None, kwargs=None
):
    """
    Purpose:
        Execute a function in a thread
    Args:
        threaded_function (Python Function): Python function to run in thread
        args (Tuple): Args for the threaded_function
        kwargs (Dict): Kwargs for the threaded_function
    Return:
        threaded_function_future (concurrent.futures Obj): Future of the threaded
            function
    """

    return thread_executor.submit(
        threaded_function,
        *(args if args is not None else []),
        **(kwargs if kwargs is not None else {}),
    )


###
# Get/Handle Result Functions
###


def get_threaded_function_result(threaded_function_future):
    """
    Purpose:
        Get result from a threaded function.

        If the function is not "done", then a "NotDone" esception will be raised
        so that the calling function knows to call later
    Args:
        threaded_function_future (concurrent.futures Obj): Future of the threaded
            function.
    Return:
        threaded_function_result (obj): return of the threaded function
    Raises:
        NotDone: the threaded function has not completed execution
    """

    if not threaded_function_future.done():
        raise ThreadedFunctionNotComplete(threaded_function_future)

    return threaded_function_future.result()


def get_threaded_function_results_as_completed(threaded_function_futures):
    """
    Purpose:
        Get results from all threaded functions. Return once all have been
        completed
    Args:
        threaded_function_futures (Dict): Dict of job names and
            concurrent.futures Objs
    Return:
        threaded_function_results (List of obj): return results of all
            threaded functions
    """

    threaded_function_results = {"return_values": {}, "exceptions": {}}

    for threaded_function_future in concurrent.futures.as_completed(
        threaded_function_futures.values()
    ):
        threaded_function_job_name = None
        for job_name, submitted_function_future in threaded_function_futures.items():
            if threaded_function_future == submitted_function_future:
                threaded_function_job_name = job_name
                break

        try:
            threaded_function_results["return_values"][
                threaded_function_job_name
            ] = get_threaded_function_result(threaded_function_future)
        # Only catch RiB exceptions. Any exceptions raised in threaded RiB functions
        # should ONLY raise RiB exceptions. If an unexpected error occurs, do not mask
        # it. Let it bubble up to the user layer and fix the bug accordingly.
        except error_utils.RIB000 as err:
            threaded_function_results["exceptions"][threaded_function_job_name] = err

    return threaded_function_results


###
# Exception Handling
###


def group_threaded_exceptions_by_type(threaded_function_results):
    """
    Purpose:
        Group Threaded exceptions by type
    Args:
        threaded_function_results (List of obj): return results of all
            threaded functions
    Return:
        errors_by_type (Dict): Exceptions by type and which jobs raised them
    """

    errors_by_type = {}

    if threaded_function_results["exceptions"]:
        for job_name, err in threaded_function_results["exceptions"].items():
            err_name = type(err).__name__
            errors_by_type.setdefault(err_name, [])
            errors_by_type[err_name].append(job_name)

    return errors_by_type
