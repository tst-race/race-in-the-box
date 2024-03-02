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

import { Intent } from '@blueprintjs/core';
import { useMutation } from '@tanstack/react-query';

import { axios } from '@/lib/axios';
import { MutationConfig, queryClient } from '@/lib/react-query';
import { getToaster } from '@/lib/toaster';
import { OperationResult } from '@/types';

import { DeploymentMode } from '../types';

import { deploymentKeys } from './queryKeys';

export const removeDeployment = ({
  mode,
  name,
}: {
  mode: DeploymentMode;
  name: string;
}): Promise<OperationResult> => axios.delete(`/api/deployments/${mode}/${name}`);

type UseRemoveDeploymentOptions = {
  config?: MutationConfig<typeof removeDeployment>;
};

export const useRemoveDeployment = ({ config }: UseRemoveDeploymentOptions) =>
  useMutation({
    onSuccess: (result: OperationResult, { mode, name }) => {
      if (result.success) {
        queryClient.refetchQueries(deploymentKeys.all(mode));
        getToaster().show({
          intent: Intent.SUCCESS,
          message: `Removed ${mode} deployment ${name}`,
        });
      } else {
        getToaster().show({
          intent: Intent.DANGER,
          message: `Unable to remove ${mode} deployment ${name}: ${result.reason}`,
        });
      }
    },
    ...config,
    mutationFn: removeDeployment,
  });
