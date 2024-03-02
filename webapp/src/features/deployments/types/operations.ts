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

import { RangeConfig } from '@/features/range-config';

type BaseDeploymentCreateRequest = {
  name: string;
  race_core: string;
  network_manager_kit: string;
  comms_channels: string[];
  comms_kits: string[];
  android_app: string;
  linux_app: string;
  node_daemon: string;
  artifact_manager_kits: string[];
  android_client_image: string;
  linux_client_image: string;
  linux_server_image: string;
  range_config: RangeConfig;
  fetch_plugins_on_start: boolean;
  no_config_gen: boolean;
  disable_config_encryption: boolean;
  cache: string;
  race_log_level: string;
};

export type LocalDeploymentCreateRequest = BaseDeploymentCreateRequest & {
  enable_gpu: boolean;
};

export type ConfigGenerationParameters = {
  network_manager_custom_args: string;
  comms_custom_args: Record<string, string>;
  artifact_manager_custom_args: Record<string, string>;
  max_iterations: number;
  force: boolean;
  skip_config_tar: boolean;
  timeout: number;
};

export type NodeOperationRequest = {
  force: boolean;
  nodes: string[] | null;
  timeout: number;
};

export type StandUpLocalDeploymentRequest = NodeOperationRequest & {
  no_publish: boolean;
};

export type StandUpAwsDeploymentRequest = NodeOperationRequest & {
  no_publish: boolean;
};

export type BootstrapNodeRequest = {
  force: boolean;
  introducer: string;
  target: string;
  passphrase: string;
  architecture: 'x86_64' | 'arm64-v8a';
  timeout: number;
};
