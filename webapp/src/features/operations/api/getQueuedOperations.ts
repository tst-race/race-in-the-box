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

import { OperationsQueuePage } from '../types';

import { operationKeys } from './queryKeys';

export const getQueuedOperations = ({
  page = 1,
  size = 20,
  target,
}: {
  page?: number;
  size?: number;
  target?: string;
}): Promise<OperationsQueuePage> =>
  axios.get(`/api/operations?${toSearchQuery({ page, size, target })}`);

type QueryFnType = typeof getQueuedOperations;

type UseQueuedOperationsOptions = {
  page?: number;
  size?: number;
  target?: string;
  config?: QueryConfig<QueryFnType>;
};

export const useQueuedOperations = ({
  page = 1,
  size = 20,
  target,
  config = {},
}: UseQueuedOperationsOptions = {}) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    ...config,
    keepPreviousData: true,
    queryKey: operationKeys.page(page, size, target),
    queryFn: () => getQueuedOperations({ page, size, target }),
  });
