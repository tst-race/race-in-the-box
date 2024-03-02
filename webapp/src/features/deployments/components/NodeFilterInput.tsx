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

import { FilterInput } from '@/components/FilterInput';

import {
  AppStatusValues,
  ArtifactsStatusValues,
  ConfigsStatusValues,
  ContainerStatusValues,
  DaemonStatusValues,
  EtcStatusValues,
  NodeStatusValues,
  RaceStatusValues,
} from '../types';

const availableFilters = {
  nodeType: {
    client: 'client',
    server: 'server',
  },
  platform: {
    linux: 'Linux',
    android: 'Android',
  },
  genesis: {
    true: 'Genesis',
    false: 'Non-genesis',
  },
  bridged: {
    true: 'Bridged',
    false: 'Managed',
  },
  artifacts: ArtifactsStatusValues,
  configs: ConfigsStatusValues,
  etc: EtcStatusValues,
  daemon: DaemonStatusValues,
  app: AppStatusValues,
  race: RaceStatusValues,
  status: NodeStatusValues,
};

const availableFiltersWithContainers = {
  ...availableFilters,
  container: ContainerStatusValues,
};

type NodeFilterInputProps = {
  filters: Record<string, string>;
  omitContainers?: boolean;
  setFilters: (filters: Record<string, string>) => void;
};

export const NodeFilterInput = ({
  filters,
  omitContainers = false,
  setFilters,
}: NodeFilterInputProps) => (
  <FilterInput
    availableFilters={omitContainers ? availableFilters : availableFiltersWithContainers}
    currentFilters={filters}
    onSetFilters={setFilters}
    placeholder="Filter nodes..."
  />
);
