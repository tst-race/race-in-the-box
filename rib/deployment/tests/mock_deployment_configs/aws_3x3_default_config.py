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
A Mock aws_3x3_default_config_dict
"""

aws_3x3_default_config_dict = {
    "name": "example_3x3_aws_deployment_obj",
    "mode": "test-rib-mode",
    "rib_version": "test-rib-version",
    "race_core": {
        "raw": "local=/race-core",
        "source_type": "local",
        "uri": "/race-core",
    },
    "android_app": {
        "name": "AndroidApp",
        "kit_type": "core",
        "source": {
            "raw": "core=android-app",
            "source_type": "core",
            "asset": "android-app",
        },
    },
    "linux_app": {
        "name": "LinuxApp",
        "kit_type": "core",
        "source": {
            "raw": "core=linux-app",
            "source_type": "core",
            "asset": "linux-app",
        },
    },
    "node_daemon": {
        "name": "NodeDaemon",
        "kit_type": "core",
        "source": {
            "raw": "core=node-daemon",
            "source_type": "core",
            "asset": "node-daemon",
        },
    },
    "network_manager_kit": {
        "name": "MockPluginNMStub",
        "kit_type": "network-manager",
        "source": {
            "raw": "core=test-network-manager-plugin",
            "source_type": "core",
            "asset": "test-network-manager-plugin",
        },
    },
    "comms_channels": [
        {
            "name": "mockTwoSixDirectCpp",
            "kit_name": "MockPluginCommsTwoSixStub",
            "enabled": True,
        },
        {
            "name": "mockTwoSixIndirectCpp",
            "kit_name": "MockPluginCommsTwoSixStub",
            "enabled": True,
        },
    ],
    "comms_kits": [
        {
            "name": "MockPluginCommsTwoSixStub",
            "kit_type": "comms",
            "source": {
                "raw": "core=test-comms-plugin",
                "source_type": "core",
                "asset": "test-comms-plugin",
            },
        },
    ],
    "artifact_manager_kits": [
        {
            "name": "MockPluginArtifactManagerTwoSixStub",
            "kit_type": "artifact-manager",
            "source": {
                "raw": "core=test-artifact-manager-plugin",
                "source_type": "core",
                "asset": "test-artifact-manager-plugin",
            },
        },
    ],
    "images": [
        {
            "tag": "race-linux-client:0.0.0",
            "platform": "linux",
            "architecture": "x86_64",
            "node_type": "client",
        },
        {
            "tag": "race-linux-server:0.0.0",
            "platform": "linux",
            "architecture": "x86_64",
            "node_type": "server",
        },
    ],
    "nodes": {
        "race-client-00001": {
            "platform": "linux",
            "architecture": "x86_64",
            "node_type": "client",
            "genesis": True,
            "bridge": False,
            "gpu": False,
        },
        "race-client-00002": {
            "platform": "linux",
            "architecture": "x86_64",
            "node_type": "client",
            "genesis": True,
            "bridge": False,
            "gpu": False,
        },
        "race-client-00003": {
            "platform": "linux",
            "architecture": "x86_64",
            "node_type": "client",
            "genesis": True,
            "bridge": False,
            "gpu": False,
        },
        "race-server-00001": {
            "platform": "linux",
            "architecture": "x86_64",
            "node_type": "server",
            "genesis": True,
            "bridge": False,
            "gpu": False,
        },
        "race-server-00002": {
            "platform": "linux",
            "architecture": "x86_64",
            "node_type": "server",
            "genesis": True,
            "bridge": False,
            "gpu": False,
        },
        "race-server-00003": {
            "platform": "linux",
            "architecture": "x86_64",
            "node_type": "server",
            "genesis": True,
            "bridge": False,
            "gpu": False,
        },
    },
    "aws_env_name": "test-aws-env-name",
    "bastion_image": "test-bastion-image",
    "race_encryption_type": "ENC_AES",
}
