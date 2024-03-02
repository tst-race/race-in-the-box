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

import { useDeploymentServiceStatus } from '../api/getDeploymentServiceStatus';
import { DeploymentMode, ServiceStatus } from '../types';

const allZeros: Record<ServiceStatus, 0> = {
  NOT_RUNNING: 0,
  RUNNING: 0,
  ERROR: 0,
  UNKNOWN: 0,
};

export type UseDeploymentServiceStatusSummaryOptions = {
  mode: DeploymentMode;
  name: string;
};

export type UseDeploymentServiceStatusSummaryResult = {
  byStatus: Record<ServiceStatus, number>;
  isLoading: boolean;
  total: number;
};

export const useDeploymentServiceStatusSummary = ({
  mode,
  name,
}: UseDeploymentServiceStatusSummaryOptions): UseDeploymentServiceStatusSummaryResult => {
  const { data, isLoading } = useDeploymentServiceStatus({ mode, name });

  const byStatus: Record<ServiceStatus, number> = useMemo(() => {
    if (data) {
      const byStatus = { ...allZeros };
      if (data.children['External Services']?.children) {
        for (const serviceStatus of Object.values(data.children['External Services'].children)) {
          byStatus[serviceStatus.status] += 1;
        }
      }
      if (data.children['RiB']?.children) {
        for (const serviceStatus of Object.values(data.children['RiB'].children)) {
          byStatus[serviceStatus.status] += 1;
        }
      }
      return byStatus;
    }
    return allZeros;
  }, [data]);

  const total = (() => {
    if (!data) {
      return 0;
    }
    let total = 0;
    if (data.children['External Services']?.children) {
      total += Object.keys(data.children['External Services'].children).length;
    }
    if (data.children['RiB']?.children) {
      total += Object.keys(data.children['RiB'].children).length;
    }
    return total;
  })();

  return {
    byStatus,
    isLoading,
    total,
  };
};
