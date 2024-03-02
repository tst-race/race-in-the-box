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

""" FastAPI app """

# Python Library Imports
import os
from fastapi import FastAPI

# Local Python Library Imports
import rib.restapi.internal.database as database
from rib.restapi.internal.operations_queue import operations_queue
from rib.restapi.routers import (
    aws_deployment,
    github_config,
    info,
    race,
    local_deployment,
    messaging,
    operations,
    templates,
)

database.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="RACE in the box",
    version=os.environ.get("RIB_VERSION", "unknown"),
)

app.include_router(github_config.router)
app.include_router(info.router)
app.include_router(race.router)
app.include_router(local_deployment.router)
app.include_router(aws_deployment.router)
app.include_router(operations.router)
app.include_router(templates.router)
app.include_router(messaging.router)


@app.on_event("startup")
def startup():
    """Start operations queue"""
    operations_queue.start()


@app.on_event("shutdown")
def shutdown():
    """Shutdown operations queue"""
    operations_queue.shutdown()
