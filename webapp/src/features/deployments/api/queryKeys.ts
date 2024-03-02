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

import { DeploymentMode } from '../types';

export const deploymentKeys = {
  all: (mode: DeploymentMode) => ['deployments', mode],
  active: (mode: DeploymentMode) => ['deployments', mode, 'active'],
  info: (mode: DeploymentMode, name: string) => ['deployments', mode, name, 'info'],
  rangeConfig: (mode: DeploymentMode, name: string) => ['deployments', mode, name, 'range-config'],
  nodeStatus: (mode: DeploymentMode, name: string) => ['deployments', mode, name, 'status', 'node'],
  containerStatus: (mode: DeploymentMode, name: string) => [
    'deployments',
    mode,
    name,
    'status',
    'container',
  ],
  serviceStatus: (mode: DeploymentMode, name: string) => [
    'deployments',
    mode,
    name,
    'status',
    'service',
  ],
  nodes: (mode: DeploymentMode, name: string, filters: Record<string, string | undefined>) => [
    'deployments',
    mode,
    name,
    'nodes',
    filters,
  ],
};
