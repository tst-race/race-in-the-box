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

import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

import {
  AppStatus,
  ArtifactsStatus,
  BoolFlag,
  ConfigsStatus,
  ContainerStatus,
  DaemonStatus,
  EtcStatus,
  NodeFilter,
  NodeStatus,
  NodeType,
  Platform,
  RaceStatus,
} from '../types';

export type UseNodeFilterResult = {
  filters: Record<string, string>;
  nodeFilter: NodeFilter;
  setFilters: (filters: Record<string, string>) => void;
};

export const useNodeFilter = (): UseNodeFilterResult => {
  const [searchParams, setSearchParams] = useSearchParams();

  const nodeFilter: NodeFilter = useMemo(
    () => ({
      nodeType: searchParams.get('nodeType') as NodeType,
      platform: searchParams.get('platform') as Platform,
      genesis: searchParams.get('genesis') as BoolFlag,
      bridged: searchParams.get('bridged') as BoolFlag,
      artifacts: searchParams.get('artifacts') as ArtifactsStatus,
      container: searchParams.get('container') as ContainerStatus,
      daemon: searchParams.get('daemon') as DaemonStatus,
      app: searchParams.get('app') as AppStatus,
      race: searchParams.get('race') as RaceStatus,
      configs: searchParams.get('configs') as ConfigsStatus,
      etc: searchParams.get('etc') as EtcStatus,
      status: searchParams.get('status') as NodeStatus,
    }),
    [searchParams]
  );

  const filters: Record<string, string> = useMemo(() => {
    const filters: Record<string, string> = {};
    Object.entries(nodeFilter).forEach(([key, value]) => {
      if (key != null && value != null) {
        filters[key] = value;
      }
    });
    return filters;
  }, [nodeFilter]);

  const setFilters = useCallback(
    (filters: Record<string, string>) => {
      for (const key in nodeFilter) {
        searchParams.delete(key);
      }
      for (const [key, value] of Object.entries(filters)) {
        searchParams.set(key, value);
      }
      setSearchParams(searchParams, { replace: true });
    },
    [nodeFilter, searchParams, setSearchParams]
  );

  return {
    filters,
    nodeFilter,
    setFilters,
  };
};
