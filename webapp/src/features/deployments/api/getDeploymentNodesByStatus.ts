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
import { toSearchQuery } from '@/utils/toSearchQuery';

import { AppStatus, DaemonStatus, DeploymentMode, NodeNameList, RaceStatus } from '../types';

import { deploymentKeys } from './queryKeys';

type ApiParams = {
  app?: AppStatus;
  daemon?: DaemonStatus;
  mode: DeploymentMode;
  name: string;
  race?: RaceStatus;
};

export const getDeploymentNodesByStatus = ({
  app,
  daemon,
  mode,
  name,
  race,
}: ApiParams): Promise<NodeNameList> =>
  axios.get(
    `/api/deployments/${mode}/${name}/nodes?${toSearchQuery({
      app,
      daemon,
      race,
    })}`
  );

type QueryFnType = typeof getDeploymentNodesByStatus;

type UseDeploymentNodesByStatusOptions = ApiParams & {
  queryConfig?: QueryConfig<QueryFnType>;
};

export const useDeploymentNodesByStatus = ({
  mode,
  name,
  queryConfig,
  app,
  daemon,
  race,
}: UseDeploymentNodesByStatusOptions) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    ...queryConfig,
    queryKey: deploymentKeys.nodes(mode, name, { app, daemon, race }),
    queryFn: () => getDeploymentNodesByStatus({ mode, name, app, daemon, race }),
  });
