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

export const NodeStatusValues = {
  READY_TO_GENERATE_CONFIG: 'ready to generate configs',
  READY_TO_TAR_CONFIGS: 'ready to create config archive',
  DOWN: 'down',
  READY_TO_PUBLISH_CONFIGS: 'ready to publish configs to file server',
  READY_TO_INSTALL_CONFIGS: 'ready to install configs on node',
  READY_TO_BOOTSTRAP: 'ready to be bootstrapped',
  READY_TO_START: 'ready to start RACE app',
  INITIALIZING: 'RACE app is initializing',
  RUNNING: 'RACE app is running',
  STOPPED: 'RACE app has been stopped',
  ERROR: 'error',
  UNKNOWN: 'unknown',
};

export type NodeStatus = keyof typeof NodeStatusValues;

export const ArtifactsStatusValues = {
  ARTIFACTS_EXIST: 'artifacts exist',
  ARTIFACT_TARS_EXIST: 'artifact archive created',
  ERROR: 'error',
};
export type ArtifactsStatus = keyof typeof ArtifactsStatusValues;

export const DaemonStatusValues = {
  NOT_REPORTING: 'not reporting',
  RUNNING: 'running',
  ERROR: 'error',
  UNKNOWN: 'unknown',
};
export type DaemonStatus = keyof typeof DaemonStatusValues;

export const AppStatusValues = {
  NOT_REPORTING: 'not reporting',
  NOT_INSTALLED: 'not installed',
  ERROR_PARTIALLY_INSTALLED: 'partially installed',
  NOT_RUNNING: 'not running',
  RUNNING: 'running',
  ERROR: 'error',
  UNKNOWN: 'unknown',
};
export type AppStatus = keyof typeof AppStatusValues;

export const RaceStatusValues = {
  NOT_REPORTING: 'not reporting',
  NOT_INITIALIZED: 'not initialized',
  NETWORK_MANAGER_NOT_READY: 'Network Manager not ready',
  RUNNING: 'running',
  UNKNOWN: 'unknown',
};
export type RaceStatus = keyof typeof RaceStatusValues;

export const ConfigsStatusValues = {
  CONFIG_GEN_SUCCESS: 'config generation successful',
  ERROR_CONFIG_GEN_FAILED: 'config generation failed',
  CONFIGS_TAR_EXISTS: 'config archive created',
  CONFIGS_TAR_PUSHED: 'config archive pushed to file server',
  DOWNLOADED_CONFIGS: 'config archive downloaded to node',
  EXTRACTED_CONFIGS: 'config archive extracted on node',
  ERROR_INVALID_CONFIGS: 'configs are invalid',
  ERROR: 'error',
  UNKNOWN: 'unknown',
};
export type ConfigsStatus = keyof typeof ConfigsStatusValues;

export const EtcStatusValues = {
  CONFIG_GEN_SUCCESS: 'config generation successful',
  ERROR_CONFIG_GEN_FAILED: 'config generation failed',
  ETC_TAR_EXISTS: 'etc archive created',
  ETC_TAR_PUSHED: 'etc archived pushed to file server',
  MISSING_REQUIRED_FILES: 'etc missing required files',
  READY: 'ready',
  ERROR: 'error',
  UNKNOWN: 'unknown',
};
export type EtcStatus = keyof typeof EtcStatusValues;

export const ContainerStatusValues = {
  NOT_PRESENT: 'not present',
  EXITED: 'exited',
  STARTING: 'starting',
  RUNNING: 'running',
  UNHEALTHY: 'unhealthy',
  UNKNOWN: 'unknown',
};
export type ContainerStatus = keyof typeof ContainerStatusValues;

export const ServiceStatusValues = {
  NOT_RUNNING: 'not running',
  RUNNING: 'running',
  ERROR: 'error',
  UNKNOWN: 'unknown',
};
export type ServiceStatus = keyof typeof ServiceStatusValues;

export type ItemStatus<T extends string> = {
  status: T;
  reason?: string;
  children?: Record<string, any>;
};

export type NodeStatusReport = {
  children: {
    app: ItemStatus<AppStatus>;
    artifacts: ItemStatus<ArtifactsStatus>;
    configs: ItemStatus<ConfigsStatus>;
    daemon: ItemStatus<DaemonStatus>;
    etc: ItemStatus<EtcStatus>;
    race: ItemStatus<RaceStatus>;
  };
  reason?: string;
  status: NodeStatus;
};

export type ParentNodeStatusReport = {
  children: Record<string, NodeStatusReport>;
  reason?: string;
  status: string;
};

export type ContainerStatusReport = {
  children: Record<string, ItemStatus<ContainerStatus>>;
  reason?: string;
  status: string;
};

export type ServiceStatusReport = {
  children: {
    'External Services': {
      children: Record<string, ItemStatus<ServiceStatus>>;
      reason?: string;
      status: string;
    };
    RiB: {
      children: Record<string, ItemStatus<ServiceStatus>>;
      reason?: string;
      status: string;
    };
  };
  reason?: string;
  status: string;
};
