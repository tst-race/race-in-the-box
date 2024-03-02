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

import { MessageListRequest, MessageListResponse } from '../types';

import { messagingKeys } from './queryKeys';

type ApiParams = MessageListRequest;

export const messageList = ({
  mode,
  name,
  search_after_vals,
  size,
  recipient,
  sender,
  test_id,
  trace_id,
  date_from,
  date_to,
  reverse_sort,
}: ApiParams): Promise<MessageListResponse> => {
  //turn the list into a string, convert back on the other end
  //remove the null starting/head element so that join works as expected
  const input_search_after_vals = `${search_after_vals}`;
  return axios.get(
    `/api/deployments/${mode}/${name}/messages/list?${toSearchQuery({
      size,
      recipient,
      sender,
      test_id,
      trace_id,
      date_from,
      date_to,
      reverse_sort,
      input_search_after_vals,
    })}`
  );
};

type QueryFnType = typeof messageList;

export type UseMessageListOptions = ApiParams & {
  config?: QueryConfig<QueryFnType>;
};

export const useMessageList = ({ config = {}, ...filters }: UseMessageListOptions) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    ...config,
    queryKey: messagingKeys.listSpecific(filters),
    keepPreviousData: true,
    queryFn: () => messageList(filters),
  });
