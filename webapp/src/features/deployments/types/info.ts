// Copyright 2023 Two Six Technologies
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//

export type ChannelConfig = {
  name: string;
  kit_name: string;
  enabled: boolean;
};

export type KitSourceType = 'core' | 'local' | 'remote' | 'gh_tag' | 'gh_branch' | 'gh_action_run';

export type KitSource = {
  raw: string;
  source_type: KitSourceType;
  uri?: string;
  org?: string;
  repo?: string;
  asset?: string;
  tag?: string;
  branch?: string;
  run?: string;
};

export type KitType = 'network-manager' | 'comms' | 'artifact-manager' | 'core';

export type KitConfig = {
  name: string;
  kit_type: KitType;
  source: KitSource;
};

export type NodeConfig = {
  architecture: 'x86_64' | 'arm64-v8a' | 'auto';
  bridge: boolean;
  genesis: boolean;
  gpu: boolean;
  node_type: 'client' | 'server';
  platform: 'android' | 'linux';
};

export type DeploymentMode = 'local' | 'aws';

export type ImageConfig = {
  architecture: 'x86_64' | 'arm64-v8a';
  node_type: 'client' | 'server';
  platform: 'android' | 'linux';
  tag: string;
};

type BaseDeploymentConfig = {
  android_app?: KitConfig;
  artifact_manager_kits: KitConfig[];
  comms_channels: ChannelConfig[];
  comms_kits: KitConfig[];
  es_metadata_index: string;
  images: ImageConfig[];
  linux_app: KitConfig;
  log_metadata_to_es: boolean;
  mode: DeploymentMode;
  name: string;
  network_manager_kit: KitConfig;
  node_daemon: KitConfig;
  nodes: Record<string, NodeConfig>;
  race_encryption_type: 'ENC_NONE' | 'ENC_AES';
  race_core: KitSource;
  registry_app?: KitConfig;
  rib_version: string;
};

export type HostEnvConfig = {
  host_os: string;
  platform: string;
  docker_engine_version: string;
  systemd_version: string;
  gpu_support: boolean;
  adb_support: boolean;
  adb_compatible: boolean;
  dev_kvm_support: boolean;
};

export type LocalDeploymentConfig = BaseDeploymentConfig & {
  android_container_acceleration: boolean;
  host_env_config: HostEnvConfig;
  tmpfs_size: number;
};

export type KitCacheMetadata = {
  source_type: KitSourceType;
  source_uri: string;
  auth: boolean;
  time: string;
  cache_path: string;
  checksum: string;
};

export type DeploymentMetadata = {
  rib_image: {
    image_tag: string;
    image_digest: string;
    image_created: string;
  };
  create_command: string;
  create_date: string;
  race_core_cache: KitCacheMetadata;
  android_app_cache: KitCacheMetadata;
  linux_app_cache: KitCacheMetadata;
  registry_app_cache?: KitCacheMetadata;
  node_daemon_cache: KitCacheMetadata;
  network_manager_kit_cache: KitCacheMetadata;
  comms_kits_cache: Record<string, KitCacheMetadata>;
  artifact_manager_kits_cache: Record<string, KitCacheMetadata>;
  last_config_gen_command?: string;
  last_config_gen_time?: string;
  last_up_command?: string;
  last_up_time?: string;
  last_start_command?: string;
  last_start_time?: string;
  last_stop_command?: string;
  last_stop_time?: string;
  last_down_command?: string;
  last_down_time?: string;
};

export type LocalDeploymentInfo = {
  config: LocalDeploymentConfig;
  metadata: DeploymentMetadata;
};

export type AwsDeploymentConfig = BaseDeploymentConfig & {
  aws_env_name: string;
};

export type AwsDeploymentInfo = {
  config: AwsDeploymentConfig;
  metadata: DeploymentMetadata;
};

export type NodeNameList = {
  nodes: string[];
};
