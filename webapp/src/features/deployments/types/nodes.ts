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

import { NodeConfig } from '@/features/range-config';

import {
  AppStatus,
  ArtifactsStatus,
  ConfigsStatus,
  ContainerStatus,
  DaemonStatus,
  EtcStatus,
  ItemStatus,
  NodeStatus,
  NodeStatusReport,
  RaceStatus,
} from './status';

export type NodeType = 'client' | 'server' | null;
export type Platform = 'linux' | 'android' | null;
export type BoolFlag = 'true' | 'false' | null;

export type NodeFilter = {
  nodeType: NodeType;
  platform: Platform;
  genesis: BoolFlag;
  bridged: BoolFlag;
  artifacts: ArtifactsStatus | null;
  container: ContainerStatus | null;
  daemon: DaemonStatus | null;
  app: AppStatus | null;
  race: RaceStatus | null;
  configs: ConfigsStatus | null;
  etc: EtcStatus | null;
  status: NodeStatus | null;
};

export type NodeAggregate = {
  name: string;
  config?: NodeConfig;
  nodeStatus?: NodeStatusReport;
  containerStatus?: ItemStatus<ContainerStatus>;
};

export type NodeActions = {
  onBootstrap: (force: boolean) => void;
  onClear: (force: boolean) => void;
  onGenerateConfigs: (force: boolean, partial: boolean) => void;
  onInstallConfigs: (force: boolean) => void;
  onPublishConfigs: (force: boolean) => void;
  onReset: (force: boolean) => void;
  onStart: (force: boolean) => void;
  onStop: (force: boolean) => void;
  onTarConfigs: (force: boolean) => void;
  onTearDown: (force: boolean) => void;
  onStandUp: (force: boolean, partial: boolean) => void;
};
