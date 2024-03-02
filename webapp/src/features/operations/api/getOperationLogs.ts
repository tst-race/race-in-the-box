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

import { OperationLogs } from '../types';

import { operationKeys } from './queryKeys';

export const getOperationLogs = ({
  id,
  offset = 0,
  limit = 1000,
}: {
  id: number;
  offset?: number;
  limit?: number;
}): Promise<OperationLogs> =>
  axios.get(`/api/operations/${id}/logs?offset=${offset}&limit=${limit}`);

type QueryFnType = typeof getOperationLogs;

type UseOperationLogsOptions = {
  id: number;
  offset?: number;
  limit?: number;
  config?: QueryConfig<QueryFnType>;
};

export const useOperationLogs = ({
  id,
  offset = 0,
  limit = 1000,
  config = {},
}: UseOperationLogsOptions) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    ...config,
    keepPreviousData: true,
    queryKey: operationKeys.logs(id, offset, limit),
    queryFn: () => getOperationLogs({ id, offset, limit }),
  });
