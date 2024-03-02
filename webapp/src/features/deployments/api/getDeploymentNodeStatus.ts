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

import { ParentNodeStatusReport, DeploymentMode } from '../types';

import { deploymentKeys } from './queryKeys';

export const getDeploymentNodeStatus = ({
  mode,
  name,
}: {
  mode: DeploymentMode;
  name: string;
}): Promise<ParentNodeStatusReport> => axios.get(`/api/deployments/${mode}/${name}/status/nodes`);

type QueryFnType = typeof getDeploymentNodeStatus;

type UseDeploymentNodeStatusOptions = {
  mode: DeploymentMode;
  name: string;
  config?: QueryConfig<QueryFnType>;
};

export const useDeploymentNodeStatus = ({
  mode,
  name,
  config = {},
}: UseDeploymentNodeStatusOptions) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    refetchInterval: 30000, // milliseconds
    ...config,
    queryKey: deploymentKeys.nodeStatus(mode, name),
    queryFn: () => getDeploymentNodeStatus({ mode, name }),
  });
