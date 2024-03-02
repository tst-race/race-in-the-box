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

import { useDeploymentContainerStatus } from '../api/getDeploymentContainerStatus';
import { DeploymentMode, ContainerStatus } from '../types';

const allZeros: Record<ContainerStatus, 0> = {
  NOT_PRESENT: 0,
  EXITED: 0,
  STARTING: 0,
  RUNNING: 0,
  UNHEALTHY: 0,
  UNKNOWN: 0,
};

export type UseDeploymentContainerStatusSummaryOptions = {
  mode: DeploymentMode;
  name: string;
};

export type UseDeploymentContainerStatusSummaryResult = {
  byStatus: Record<ContainerStatus, number>;
  isLoading: boolean;
  total: number;
};

export const useDeploymentContainerStatusSummary = ({
  mode,
  name,
}: UseDeploymentContainerStatusSummaryOptions): UseDeploymentContainerStatusSummaryResult => {
  const { data, isLoading } = useDeploymentContainerStatus({ mode, name });

  const byStatus: Record<ContainerStatus, number> = useMemo(() => {
    if (data) {
      const byStatus = { ...allZeros };
      for (const containerStatus of Object.values(data.children)) {
        byStatus[containerStatus.status] += 1;
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
