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

import { useQuery } from '@tanstack/react-query';

import { axios } from '@/lib/axios';
import { ExtractFnReturnType, QueryConfig } from '@/lib/react-query';

import { DeploymentMode, ServiceStatusReport } from '../types';

import { deploymentKeys } from './queryKeys';

export const getDeploymentServiceStatus = ({
  mode,
  name,
}: {
  mode: DeploymentMode;
  name: string;
}): Promise<ServiceStatusReport> => axios.get(`/api/deployments/${mode}/${name}/status/services`);

type QueryFnType = typeof getDeploymentServiceStatus;

type UseDeploymentServiceStatusOptions = {
  mode: DeploymentMode;
  name: string;
  config?: QueryConfig<QueryFnType>;
};

export const useDeploymentServiceStatus = ({
  mode,
  name,
  config = {},
}: UseDeploymentServiceStatusOptions) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    refetchInterval: 30000, // milliseconds
    ...config,
    queryKey: deploymentKeys.serviceStatus(mode, name),
    queryFn: () => getDeploymentServiceStatus({ mode, name }),
  });