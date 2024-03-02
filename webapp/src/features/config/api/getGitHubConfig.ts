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

import { GitHubConfig } from '../types';

import { configKeys } from './queryKeys';

export const getGitHubConfig = (): Promise<GitHubConfig> => axios.get('/api/github-config');

type QueryFnType = typeof getGitHubConfig;

type UseGitHubConfigOptions = {
  config?: QueryConfig<QueryFnType>;
};

export const useGitHubConfig = ({ config = {} }: UseGitHubConfigOptions = {}) =>
  useQuery<ExtractFnReturnType<QueryFnType>>({
    ...config,
    queryKey: configKeys.gitHubConfig,
    queryFn: getGitHubConfig,
  });