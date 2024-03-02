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

import { useMemo } from 'react';

import { RangeConfig } from '@/features/range-config';

import { useDeploymentContainerStatus } from '../api/getDeploymentContainerStatus';
import { useDeploymentNodeStatus } from '../api/getDeploymentNodeStatus';
import { useDeploymentRangeConfig } from '../api/getDeploymentRangeConfig';
import {
  ContainerStatusReport,
  DeploymentMode,
  NodeAggregate,
  NodeFilter,
  ParentNodeStatusReport,
} from '../types';

const createAggregates = (
  rangeConfig?: RangeConfig,
  nodeStatus?: ParentNodeStatusReport,
  containerStatus?: ContainerStatusReport
): NodeAggregate[] => {
  let nodes: NodeAggregate[] = [];
  if (rangeConfig) {
    nodes = rangeConfig.range.RACE_nodes.map((config) => ({ name: config.name, config }));
  } else if (nodeStatus) {
    nodes = Object.keys(nodeStatus.children)
      .sort()
      .map((name) => ({ name }));
  } else if (containerStatus) {
    nodes = Object.keys(containerStatus.children)
      .sort()
      .map((name) => ({ name }));
  }

  if (nodeStatus) {
    nodes.forEach((node) => {
      node.nodeStatus = nodeStatus.children[node.name];
    });
  }

  if (containerStatus) {
    nodes.forEach((node) => {
      node.containerStatus = containerStatus.children[node.name];
    });
  }

  return nodes;
};

type NodeFilterFunc = (node: NodeAggregate) => boolean;

const asBool = (val: string) => val == 'true';

const createFilter = (filter?: NodeFilter): NodeFilterFunc => {
  if (filter == undefined) {
    return () => true;
  }
  return (node: NodeAggregate) => {
    if (node.config) {
      if (filter.nodeType && filter.nodeType != node.config.type) return false;
      if (filter.platform && filter.platform != node.config.platform) return false;
      if (filter.genesis && asBool(filter.genesis) != node.config.genesis) return false;
      if (filter.bridged && asBool(filter.bridged) != node.config.bridge) return false;
    }
    if (node.containerStatus) {
      if (filter.container && filter.container != node.containerStatus.status) return false;
    }
    if (node.nodeStatus) {
      if (filter.status && filter.status != node.nodeStatus.status) return false;
      if (filter.daemon && filter.daemon != node.nodeStatus.children.daemon.status) return false;
      if (filter.app && filter.app != node.nodeStatus.children.app.status) return false;
      if (filter.artifacts && filter.artifacts != node.nodeStatus.children.artifacts.status)
        return false;
      if (filter.race && filter.race != node.nodeStatus.children.race.status) return false;
      if (filter.configs && filter.configs != node.nodeStatus.children.configs.status) return false;
      if (filter.etc && filter.etc != node.nodeStatus.children.etc.status) return false;
    }
    return true;
  };
};

type UseDeploymentNodesOptions = {
  filter?: NodeFilter;
  mode: DeploymentMode;
  name: string;
  omitContainers?: boolean;
};

export type UseDeploymentNodesResult = {
  isLoading: boolean;
  nodes: NodeAggregate[];
};

export const useDeploymentNodes = ({
  filter,
  mode,
  name,
  omitContainers = false,
}: UseDeploymentNodesOptions): UseDeploymentNodesResult => {
  const rangeConfig = useDeploymentRangeConfig({ mode, name });
  const nodeStatus = useDeploymentNodeStatus({ mode, name });
  const containerStatus = useDeploymentContainerStatus({
    mode,
    name,
    config: {
      enabled: !omitContainers,
    },
  });

  const nodeAggregates = useMemo(
    () => createAggregates(rangeConfig.data, nodeStatus.data, containerStatus.data),
    [rangeConfig.data, nodeStatus.data, containerStatus.data]
  );
  const nodeFilter = useMemo(() => createFilter(filter), [filter]);
  const nodes = useMemo(() => nodeAggregates.filter(nodeFilter), [nodeAggregates, nodeFilter]);

  return {
    isLoading: rangeConfig.isLoading && nodeStatus.isLoading && containerStatus.isLoading,
    nodes,
  };
};
