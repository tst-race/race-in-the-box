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
    Utilities for interacting with a Redis service
"""

# Python Library Imports
import logging
import redis
from typing import Optional

# Local Python Library Imports


###
# Globals
###


logger = logging.getLogger(__name__)


###
# Functions
###


def create_redis_client(
    host: str,
    port: int = 6379,
    db: int = 0,
) -> Optional[redis.Redis]:
    """
    Purpose:
        Create an instance of a Redis client
    Args:
        host: Hostname of the Redis servier
        port: Port on the Redis server
        db: Index of the Redis database to use
    Returns:
        Redis client, if successful in connecting to the Redis server
    """

    try:
        return redis.Redis(host=host, port=port, db=db, decode_responses=True)
    except redis.exceptions.ConnectionError as err:
        logger.error(f"Unable to connect to Redis: {err}")
    except Exception as err:
        logger.error(f"Error creating Redis client: {err}")
    return None


def is_connected(client: Optional[redis.Redis]) -> bool:
    """
    Purpose:
        Check if the given Redis client is connected to its server
    Args:
        client: Redis client
    Returns:
        True if client is valid and connected
    """
    try:
        if not client:
            return False
        return client.ping()
    except Exception as err:
        logger.debug(f"Error checking client connectivity: {err}")
        return False
