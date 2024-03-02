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

import { EnclaveInstanceTemplateList } from '../types';

import { templateKeys } from './queryKeys';

export const getEnclaveInstanceTemplates = (): Promise<EnclaveInstanceTemplateList> =>
  axios.get('/api/templates/enclave-instances');

type QueryFnType = typeof getEnclaveInstanceTemplates;

type UseEnclaveInstanceTemplatesOptions = {
  config?: QueryConfig<QueryFnType>;
};

export const useEnclaveInstanceTemplates = ({ config = {} }: UseEnclaveInstanceTemplatesOptions) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    ...config,
    queryKey: templateKeys.all('enclave-instances'),
    queryFn: () => getEnclaveInstanceTemplates(),
  });
