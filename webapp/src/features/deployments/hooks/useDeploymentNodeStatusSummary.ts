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

import { useDeploymentNodeStatus } from '../api/getDeploymentNodeStatus';
import { DeploymentMode, NodeStatus } from '../types';

const allZeros: Record<NodeStatus, 0> = {
  READY_TO_GENERATE_CONFIG: 0,
  READY_TO_TAR_CONFIGS: 0,
  DOWN: 0,
  READY_TO_PUBLISH_CONFIGS: 0,
  READY_TO_INSTALL_CONFIGS: 0,
  READY_TO_BOOTSTRAP: 0,
  READY_TO_START: 0,
  INITIALIZING: 0,
  RUNNING: 0,
  STOPPED: 0,
  ERROR: 0,
  UNKNOWN: 0,
};

export type UseDeploymentNodeStatusSummaryOptions = {
  mode: DeploymentMode;
  name: string;
};

export type UseDeploymentNodeStatusSummaryResult = {
  byStatus: Record<NodeStatus, number>;
  isLoading: boolean;
  total: number;
};

export const useDeploymentNodeStatusSummary = ({
  mode,
  name,
}: UseDeploymentNodeStatusSummaryOptions): UseDeploymentNodeStatusSummaryResult => {
  const { data, isLoading } = useDeploymentNodeStatus({ mode, name });

  const byStatus: Record<NodeStatus, number> = useMemo(() => {
    if (data) {
      const byStatus = { ...allZeros };
      for (const nodeStatus of Object.values(data.children)) {
        byStatus[nodeStatus.status] += 1;
      }
      return byStatus;
    }
    return allZeros;
  }, [data]);

  return {
    byStatus,
    isLoading,
    total: data ? Object.keys(data.children).length : 0,
  };
};
