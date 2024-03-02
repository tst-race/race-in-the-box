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

import { EnclaveInstanceTemplate } from '../types';

import { templateKeys } from './queryKeys';

export const getEnclaveInstanceTemplate = ({
  name,
}: {
  name: string;
}): Promise<EnclaveInstanceTemplate> => axios.get(`/api/templates/enclave-instances/${name}`);

type QueryFnType = typeof getEnclaveInstanceTemplate;

type UseEnclaveInstanceTemplateOptions = {
  name: string;
  config?: QueryConfig<QueryFnType>;
};

export const useEnclaveInstanceTemplate = ({
  name,
  config = {},
}: UseEnclaveInstanceTemplateOptions) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    ...config,
    queryKey: templateKeys.one('enclave-instances', name),
    queryFn: () => getEnclaveInstanceTemplate({ name }),
  });
