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

import { AwsDeploymentInfo } from '../types';

import { deploymentKeys } from './queryKeys';

export const getAwsDeploymentInfo = ({ name }: { name: string }): Promise<AwsDeploymentInfo> =>
  axios.get(`/api/deployments/aws/${name}/info`);

type QueryFnType = typeof getAwsDeploymentInfo;

type UseAwsDeploymentInfoOptions = {
  name: string;
  config?: QueryConfig<QueryFnType>;
};

export const useAwsDeploymentInfo = ({ name, config = {} }: UseAwsDeploymentInfoOptions) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    ...config,
    queryKey: deploymentKeys.info('aws', name),
    queryFn: () => getAwsDeploymentInfo({ name }),
  });
