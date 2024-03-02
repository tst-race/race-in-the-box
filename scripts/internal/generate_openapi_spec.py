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
# Script to generate OpenAPI spec for the REST API
#
# Example:
#     generate_openapi_spec.py spec.json
# -----------------------------------------------------------------------------

import click
import json
import sys
from fastapi.openapi.utils import get_openapi
from typing import IO

from rib.restapi.main import app

@click.command()
@click.argument("out-file", default=sys.stdout, type=click.File("w"))
def generate_openapi_spec(out_file: IO):
    """
    Generate OpenAPI spec for the REST API
    """
    json.dump(get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    ), out_file)


if __name__ == "__main__":
    generate_openapi_spec()
