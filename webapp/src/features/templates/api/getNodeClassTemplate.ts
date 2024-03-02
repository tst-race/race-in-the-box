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

import { UseQueryOptions, useQueries, useQuery } from '@tanstack/react-query';

import { axios } from '@/lib/axios';
import { ExtractFnReturnType, QueryConfig } from '@/lib/react-query';

import { NodeClassTemplate } from '../types';

import { templateKeys } from './queryKeys';

export const getNodeClassTemplate = ({ name }: { name: string }): Promise<NodeClassTemplate> =>
  axios.get(`/api/templates/node-classes/${name}`);

type QueryFnType = typeof getNodeClassTemplate;

type UseNodeClassTemplateOptions = {
  name: string;
  config?: QueryConfig<QueryFnType>;
};

export const useNodeClassTemplate = ({ name, config = {} }: UseNodeClassTemplateOptions) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    ...config,
    queryKey: templateKeys.one('node-classes', name),
    queryFn: () => getNodeClassTemplate({ name }),
  });

type UseFetchNodeClassTemplatesOptions = {
  names: string[];
  config?: QueryConfig<QueryFnType>;
};

export const useFetchNodeClassTemplates = ({
  names,
  config = {},
}: UseFetchNodeClassTemplatesOptions) =>
  useQueries({
    queries: names.map<UseQueryOptions<ExtractFnReturnType<QueryFnType>>>((name) => ({
      ...config,
      queryKey: templateKeys.one('node-classes', name),
      queryFn: () => getNodeClassTemplate({ name }),
    })),
  });
