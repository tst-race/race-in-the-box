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

import { NodeCounts } from '@/features/range-config';
import { boolKey } from '@/utils/boolKey';

import { useAwsDeploymentInfo } from '../api/getAwsDeploymentInfo';
import { AwsDeploymentInfo } from '../types';

export type UseAwsDeploymentConfigSummaryOptions = {
  name: string;
};

export type UseAwsDeploymentConfigSummaryResult = {
  info: AwsDeploymentInfo | null;
  isLoading: boolean;
  nodeCounts: NodeCounts;
};

export const useAwsDeploymentConfigSummary = ({ name }: UseAwsDeploymentConfigSummaryOptions) => {
  const { data, isLoading } = useAwsDeploymentInfo({ name });

  const nodeCounts = useMemo(() => {
    const counts: NodeCounts = {
      type: { client: 0, server: 0 },
      platform: { linux: 0, android: 0 },
      genesis: { true: 0, false: 0 },
      bridge: { true: 0, false: 0 },
    };

    if (data) {
      for (const nodeConfig of Object.values(data.config.nodes)) {
        counts.type[nodeConfig.node_type] += 1;
        counts.platform[nodeConfig.platform] += 1;
        counts.genesis[boolKey(nodeConfig.genesis)] += 1;
        counts.bridge[boolKey(nodeConfig.bridge)] += 1;
      }
    }

    return counts;
  }, [data]);

  return {
    info: data,
    isLoading,
    nodeCounts,
  };
};
