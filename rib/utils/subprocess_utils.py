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
    Utilities for executing subprocess commands
"""

# Python Library Imports
import logging
import os
import subprocess
import threading
from typing import Optional

# Local Python Library Imports
from rib.utils.log_utils import TRACE


default_logger = logging.getLogger(__name__)


class LogPipe(threading.Thread):
    """File-like object and pipe to record all output written to it to the logger"""

    def __init__(self, logger: logging.Logger, level: int, capture: bool = False):
        """Initializes the pipe to write to the given logger at the given level"""
        super().__init__()

        self.daemon = False
        self.level = level
        self.logger = logger
        self.fdRead, self.fdWrite = os.pipe()
        self.reader = os.fdopen(self.fdRead)
        self.buffer = [] if capture else None
        self.start()

    def fileno(self):
        """Return the file number of the write sice of the pipe"""
        return self.fdWrite

    def run(self):
        """Reads from the pipe and records with the logger"""
        for line in iter(self.reader.readline, ""):
            self.logger.log(self.level, line.strip("\n"))
            if self.buffer is not None:
                self.buffer.append(line.strip("\n"))
        self.reader.close()

    def close(self):
        """Closes the pipe"""
        os.close(self.fdWrite)

    def write(self, message):
        """Writes the given message to the logger"""
        self.logger.log(self.level, message)

    def flush(self):
        """Does nothing"""
        pass


def run(
    *args,
    capture_output: bool = False,
    check: bool = False,
    logger: Optional[logging.Logger] = None,
    stderr_level: int = logging.WARN,
    stdout_level: int = TRACE,
    timeout: Optional[int] = None,
    **kwargs,
) -> subprocess.CompletedProcess:
    """
    Purpose:
        Run subprocess command and return the result. By default, stdout and stderr is
        logged.
    Args:
        args: Positional args forwarded to the subprocess.Popen constructor
        capture_output: If True, include standard output/error in returned CompletedProcess
            (otherwise output is logged but not returned)
        check: Raise an exception if the command exits with a non-zero return code
        logger: Logger to use for logging stdout and stderr
        stderr_level: Log level to use for stderr
        stdout_level: Log level to use for stdout
        timeout: Number of seconds to allow the command to run before timing out
        kwargs: Keyword args forwarded to the subprocess.Popen constructor
    Returns:
        Completed process
    """
    if not logger:
        logger = default_logger

    stdout_pipe = None
    stdout = kwargs.pop("stdout", None)
    if not stdout:
        stdout_pipe = LogPipe(logger, stdout_level, capture=capture_output)
        stdout = stdout_pipe

    stderr_pipe = None
    stderr = kwargs.pop("stderr", None)
    if not stderr:
        stderr_pipe = LogPipe(logger, stderr_level, capture=capture_output)
        stderr = stderr_pipe

    try:
        proc = subprocess.Popen(*args, stderr=stderr, stdout=stdout, **kwargs)
        stdout_data, stderr_data = proc.communicate(timeout=timeout)
        if check and proc.returncode:
            raise subprocess.CalledProcessError(
                proc.returncode, proc.args, output=proc.stdout, stderr=proc.stderr
            )
    finally:
        if stdout_pipe:
            stdout_pipe.close()

        if stderr_pipe:
            stderr_pipe.close()

    if stdout_pipe and capture_output:
        stdout_data = "\n".join(stdout_pipe.buffer)

    if stderr_pipe and capture_output:
        stderr_data = "\n".join(stderr_pipe.buffer)

    return subprocess.CompletedProcess(
        proc.args, proc.returncode, stdout=stdout_data, stderr=stderr_data
    )
