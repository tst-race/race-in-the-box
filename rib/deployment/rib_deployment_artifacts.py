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
    Artifact-handling helpers for a deployment
"""

# Python Library Imports
from dataclasses import dataclass
from typing import Dict, List, Optional

# Local Python Library Imports
from rib.utils import error_utils, plugin_utils


###
# Types
###


@dataclass
class KitCacheAndConfig:
    """Kit cache metadata and config after downloading all depoyment kit sources"""

    race_core_cache: plugin_utils.KitCacheMetadata
    android_app_cache: Optional[plugin_utils.KitCacheMetadata]
    android_app_config: Optional[plugin_utils.KitConfig]
    linux_app_cache: plugin_utils.KitCacheMetadata
    linux_app_config: plugin_utils.KitConfig
    node_daemon_cache: plugin_utils.KitCacheMetadata
    node_daemon_config: plugin_utils.KitConfig
    network_manager_kit_cache: plugin_utils.KitCacheMetadata
    network_manager_kit_config: plugin_utils.KitConfig
    comms_kits_cache: Dict[str, plugin_utils.KitCacheMetadata]
    comms_kits_config: List[plugin_utils.KitConfig]
    artifact_manager_kits_cache: Dict[str, plugin_utils.KitCacheMetadata]
    artifact_manager_kits_config: List[plugin_utils.KitConfig]
    channels_to_kits: Dict[str, str]
    registry_app_cache: Optional[plugin_utils.KitCacheMetadata] = None
    registry_app_config: Optional[plugin_utils.KitConfig] = None


###
# Functions
###


def download_deployment_kits(
    cache: plugin_utils.CacheStrategy,
    race_core: plugin_utils.KitSource,
    android_app: Optional[plugin_utils.KitSource],
    linux_app: plugin_utils.KitSource,
    node_daemon: plugin_utils.KitSource,
    registry_app: Optional[plugin_utils.KitSource],
    network_manager_kit: plugin_utils.KitSource,
    comms_channels: List[str],
    comms_kits: List[plugin_utils.KitSource],
    artifact_manager_kits: List[plugin_utils.KitSource],
) -> KitCacheAndConfig:
    """
    Purpose:
        Download all kits for a deployment

    Args:
        cache: Cache strategy
        race_core: Source for race-core
        android_app: Source for the RACE Android app, or None if Android is not required
        linux_app: Source for the RACE Linux app
        node_daemon: Source for the node daemon app
        registry_app: Source for the RACE registry app
        network_manager_kit: Source for the network manager kit
        comms_channels: List of comms channel names
        comms_kits: List of sources for the comms kits
        artifact_manager_kits: List of sources for the artifact manager kits

    Returns:
        Cache metadata and kit config for each kit
    """

    # Download RACE core
    race_core_cache = plugin_utils.download_race_core(race_core, cache)

    # Download apps
    if android_app:
        android_app_cache = plugin_utils.download_kit(
            "Android app", android_app, race_core_cache, cache
        )
        android_app_config = plugin_utils.KitConfig(
            name="AndroidApp", kit_type=plugin_utils.KitType.APP, source=android_app
        )
    else:
        android_app_cache = None
        android_app_config = None

    linux_app_cache = plugin_utils.download_kit(
        "Linux app", linux_app, race_core_cache, cache
    )
    linux_app_config = plugin_utils.KitConfig(
        name="LinuxApp", kit_type=plugin_utils.KitType.APP, source=linux_app
    )

    node_daemon_cache = plugin_utils.download_kit(
        "Node daemon", node_daemon, race_core_cache, cache
    )
    node_daemon_config = plugin_utils.KitConfig(
        name="NodeDaemon", kit_type=plugin_utils.KitType.APP, source=node_daemon
    )

    if registry_app:
        registry_app_cache = plugin_utils.download_kit(
            "Registry app", registry_app, race_core_cache, cache
        )
        registry_app_config = plugin_utils.KitConfig(
            name="RegistryApp",
            kit_type=plugin_utils.KitType.APP,
            source=registry_app,
        )
    else:
        registry_app_cache = None
        registry_app_config = None

    # Download network manager kit
    network_manager_kit_cache = plugin_utils.download_kit(
        "Network manager kit", network_manager_kit, race_core_cache, cache
    )
    network_manager_kit_config = plugin_utils.create_kit_config(
        "Network manager kit",
        plugin_utils.KitType.NETWORK_MANAGER,
        network_manager_kit,
        network_manager_kit_cache,
    )

    # Download comms kits
    comms_kits_cache: Dict[str, plugin_utils.KitCacheMetadata] = {}
    comms_kits_config: List[plugin_utils.KitConfig] = []
    for kit_source in comms_kits:
        kit_cache = plugin_utils.download_kit(
            "Comms kit", kit_source, race_core_cache, cache
        )
        kit_config = plugin_utils.create_kit_config(
            "Comms kit",
            plugin_utils.KitType.COMMS,
            kit_source,
            kit_cache,
        )
        if kit_config.name in comms_kits_cache:
            # Duplicate kit found
            raise error_utils.RIB506("comms kit", kit_config.name)
        comms_kits_cache[kit_config.name] = kit_cache
        comms_kits_config.append(kit_config)

    # Download artifact manager kits
    artifact_manager_kits_cache: Dict[str, plugin_utils.KitCacheMetadata] = {}
    artifact_manager_kits_config: List[plugin_utils.KitConfig] = []
    for kit_source in artifact_manager_kits:
        kit_cache = plugin_utils.download_kit(
            "Artifact manager kit", kit_source, race_core_cache, cache
        )
        kit_config = plugin_utils.create_kit_config(
            "Artifact manager kit",
            plugin_utils.KitType.ARTIFACT_MANAGER,
            kit_source,
            kit_cache,
        )
        if kit_config.name in artifact_manager_kits_cache:
            # Duplicate kit found
            raise error_utils.RIB506("artifact manager kit", kit_config.name)
        artifact_manager_kits_cache[kit_config.name] = kit_cache
        artifact_manager_kits_config.append(kit_config)

    # Determine mapping of channel to kit
    channels_to_kits: Dict[str, str] = {}
    for kit_name, kit_cache in comms_kits_cache.items():
        kit_channels = plugin_utils.get_channel_names(kit_name, kit_cache)
        for kit_channel in kit_channels:
            if kit_channel in comms_channels:
                if kit_channel in channels_to_kits:
                    # Duplicate channel found
                    raise error_utils.RIB506("comms channel", kit_channel)
                channels_to_kits[kit_channel] = kit_name
            # else not a channel configured for this deployment

    missing_channels = set(comms_channels) - set(channels_to_kits)
    if missing_channels:
        raise error_utils.RIB508("channel", missing_channels)

    return KitCacheAndConfig(
        race_core_cache=race_core_cache,
        android_app_cache=android_app_cache,
        android_app_config=android_app_config,
        linux_app_cache=linux_app_cache,
        linux_app_config=linux_app_config,
        node_daemon_cache=node_daemon_cache,
        node_daemon_config=node_daemon_config,
        registry_app_cache=registry_app_cache,
        registry_app_config=registry_app_config,
        network_manager_kit_cache=network_manager_kit_cache,
        network_manager_kit_config=network_manager_kit_config,
        comms_kits_cache=comms_kits_cache,
        comms_kits_config=comms_kits_config,
        artifact_manager_kits_cache=artifact_manager_kits_cache,
        artifact_manager_kits_config=artifact_manager_kits_config,
        channels_to_kits=channels_to_kits,
    )


def validate_compositions(plugins: List[Dict], compositions: List[Dict]) -> None:
    all_encodings = {}
    all_transports = {}
    all_usermodels = {}

    # Build mapping of components to plugins, checking for duplicates
    for plugin in plugins:
        for encoding in plugin.get("encodings", []):
            plugin_name = plugin["file_path"]
            if all_encodings.get(encoding, plugin_name) != plugin_name:
                # Duplicate encoding component found
                raise error_utils.RIB506("encoding component", encoding)
            all_encodings[encoding] = plugin_name

        for transport in plugin.get("transports", []):
            plugin_name = plugin["file_path"]
            if all_transports.get(transport, plugin_name) != plugin_name:
                # Duplicate transport component found
                raise error_utils.RIB506("transport component", transport)
            all_transports[transport] = plugin_name

        for usermodel in plugin.get("usermodels", []):
            plugin_name = plugin["file_path"]
            if all_usermodels.get(usermodel, plugin_name) != plugin_name:
                # Duplicate usermodel component found
                raise error_utils.RIB506("usermodel component", usermodel)
            all_usermodels[usermodel] = plugin_name

    # Make sure all composition components are satisfied
    missing = set()
    for composition in compositions:
        for encoding in composition["encodings"]:
            if encoding not in all_encodings:
                missing.add(encoding)
        if composition["transport"] not in all_transports:
            missing.add(composition["transport"])
        if composition["usermodel"] not in all_usermodels:
            missing.add(composition["usermodel"])

    if missing:
        raise error_utils.RIB508("component", missing)
