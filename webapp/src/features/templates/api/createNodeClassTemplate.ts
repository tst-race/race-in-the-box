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

import { NodeClassTemplate } from '../types';

import { templateKeys } from './queryKeys';

export const createNodeClassTemplate = ({ data }: { data: NodeClassTemplate }) =>
  axios.post('/api/templates/node-classes', data);

type UseCreateNodeClassTemplateOptions = {
  config?: MutationConfig<typeof createNodeClassTemplate>;
};

export const useCreateNodeClassTemplate = ({ config }: UseCreateNodeClassTemplateOptions = {}) =>
  useMutation({
    onSuccess: (_, { data }) => {
      queryClient.invalidateQueries(templateKeys.all('node-classes'));
      getToaster().show({
        intent: Intent.SUCCESS,
        message: `Added node class template ${data.name}`,
      });
    },
    ...config,
    mutationFn: createNodeClassTemplate,
  });
