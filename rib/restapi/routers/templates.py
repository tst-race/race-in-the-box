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

""" RiB /api/templates router """

# Python Library Imports
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from typing import List

# Local Python Library Imports
from rib.restapi.internal.jsonfiles import JsonFiles

router = APIRouter(
    prefix="/api/templates",
    tags=["Deployment templates"],
    responses={404: {"description": "Not found"}},
)

###
# Dependencies
###


def get_node_classes() -> JsonFiles:
    """Node class templates JSON files"""
    return JsonFiles("/root/.race/rib/ui/templates/node-classes")


def get_enclave_classes() -> JsonFiles:
    """Enclave class templates JSON files"""
    return JsonFiles("/root/.race/rib/ui/templates/enclave-classes")


def get_enclave_instances() -> JsonFiles:
    """Enclave instance templates JSON files"""
    return JsonFiles("/root/.race/rib/ui/templates/enclave-instances")


###
# Node class templates
###


class NodeClassTemplate(BaseModel):
    """Node class template"""

    name: str
    type: str
    nat: bool
    genesis: bool
    gpu: bool
    bridge: bool
    platform: str
    architecture: str
    environment: str


class NodeClassTemplateList(BaseModel):
    """List of node class templates"""

    nodeClasses: List[str]


@router.post("/node-classes", status_code=201)
def create_node_class(
    data: NodeClassTemplate, node_classes: JsonFiles = Depends(get_node_classes)
):
    """Create node class template"""

    data_json = jsonable_encoder(data)
    node_classes.create(data.name, data_json)


@router.get("/node-classes", response_model=NodeClassTemplateList)
def list_node_classes(node_classes: JsonFiles = Depends(get_node_classes)):
    """Get list of node class templates"""

    return {"nodeClasses": node_classes.get_all()}


@router.get("/node-classes/{name}", response_model=NodeClassTemplate)
def get_node_class(name: str, node_classes: JsonFiles = Depends(get_node_classes)):
    """Get node class template"""

    return node_classes.get(name)


@router.put("/node-classes/{name}")
def update_node_class(
    name: str,
    data: NodeClassTemplate,
    node_classes: JsonFiles = Depends(get_node_classes),
):
    """Update node class template"""

    data_json = jsonable_encoder(data)
    data_json["name"] = name  # don't allow renaming
    node_classes.update(name, data_json)


@router.delete("/node-classes/{name}", status_code=204)
def delete_node_class(name: str, node_classes: JsonFiles = Depends(get_node_classes)):
    """Delete node class template"""

    node_classes.remove(name)


###
# Enclave class templates
###


class PortMappingTemplate(BaseModel):
    """Enclave port mappting"""

    startExternalPort: int
    internalPort: int


class NodeInstanceTemplate(BaseModel):
    """Enclave node instances"""

    nodeClassName: str
    nodeQuantity: int
    portMapping: List[PortMappingTemplate]


class EnclaveClassTemplate(BaseModel):
    """Enclave class template"""

    name: str
    nodes: List[NodeInstanceTemplate]


class EnclaveClassTemplateList(BaseModel):
    """List of enclave class templates"""

    enclaveClasses: List[str]


@router.post("/enclave-classes", status_code=201)
def create_enclave_class(
    data: EnclaveClassTemplate,
    enclave_classes: JsonFiles = Depends(get_enclave_classes),
):
    """Create enclave class template"""

    data_json = jsonable_encoder(data)
    enclave_classes.create(data.name, data_json)


@router.get("/enclave-classes", response_model=EnclaveClassTemplateList)
def list_enclave_classes(enclave_classes: JsonFiles = Depends(get_enclave_classes)):
    """Get list of enclave class templates"""

    return {"enclaveClasses": enclave_classes.get_all()}


@router.get("/enclave-classes/{name}", response_model=EnclaveClassTemplate)
def get_enclave_class(
    name: str, enclave_classes: JsonFiles = Depends(get_enclave_classes)
):
    """Get enclave class template"""

    return enclave_classes.get(name)


@router.put("/enclave-classes/{name}")
def update_enclave_class(
    name: str,
    data: EnclaveClassTemplate,
    enclave_classes: JsonFiles = Depends(get_enclave_classes),
):
    """Update enclave class template"""

    data_json = jsonable_encoder(data)
    data_json["name"] = name  # don't allow renaming
    enclave_classes.update(name, data_json)


@router.delete("/enclave-classes/{name}", status_code=204)
def delete_enclave_class(
    name: str, enclave_classes: JsonFiles = Depends(get_enclave_classes)
):
    """Delete enclave class template"""

    enclave_classes.remove(name)


###
# Enclave instance templates
###


class EnclaveInstanceTemplate(BaseModel):
    """Enclave instance template"""

    name: str
    enclaveClassName: str
    enclaveQuantity: int


class EnclaveInstanceTemplateList(BaseModel):
    """List of enclave instance templates"""

    enclaveInstances: List[str]


@router.post("/enclave-instances", status_code=201)
def create_enclave_instance(
    data: EnclaveInstanceTemplate,
    enclave_instances: JsonFiles = Depends(get_enclave_instances),
):
    """Create enclave instance template"""

    data_json = jsonable_encoder(data)
    enclave_instances.create(data.name, data_json)


@router.get("/enclave-instances", response_model=EnclaveInstanceTemplateList)
def list_enclave_instances(
    enclave_instances: JsonFiles = Depends(get_enclave_instances),
):
    """Get list of enclave instance templates"""

    return {"enclaveInstances": enclave_instances.get_all()}


@router.get("/enclave-instances/{name}", response_model=EnclaveInstanceTemplate)
def get_enclave_instance(
    name: str, enclave_instances: JsonFiles = Depends(get_enclave_instances)
):
    """Get enclave instance template"""

    return enclave_instances.get(name)


@router.put("/enclave-instances/{name}")
def update_enclave_instance(
    name: str,
    data: EnclaveInstanceTemplate,
    enclave_instances: JsonFiles = Depends(get_enclave_instances),
):
    """Update enclave instance template"""

    data_json = jsonable_encoder(data)
    data_json["name"] = name  # don't allow renaming
    enclave_instances.update(name, data_json)


@router.delete("/enclave-instances/{name}", status_code=204)
def delete_enclave_instance(
    name: str, enclave_instances: JsonFiles = Depends(get_enclave_instances)
):
    """Delete enclave instance template"""

    enclave_instances.remove(name)
