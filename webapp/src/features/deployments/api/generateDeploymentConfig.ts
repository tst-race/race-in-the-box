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

import { useMutation } from '@tanstack/react-query';

import { axios } from '@/lib/axios';
import { MutationConfig } from '@/lib/react-query';
import { OperationQueuedResult } from '@/types';

import { DeploymentMode, ConfigGenerationParameters } from '../types';

export const generateDeploymentConfig = ({
  data,
  mode,
  name,
}: {
  data: ConfigGenerationParameters;
  mode: DeploymentMode;
  name: string;
}): Promise<OperationQueuedResult> =>
  axios.post(`/api/deployments/${mode}/${name}/operations/generate-configs`, data);

type UseGenerateDeploymentConfigOptions = {
  config?: MutationConfig<typeof generateDeploymentConfig>;
};

export const useGenerateDeploymentConfig = ({ config }: UseGenerateDeploymentConfigOptions = {}) =>
  useMutation({
    ...config,
    mutationFn: generateDeploymentConfig,
  });
