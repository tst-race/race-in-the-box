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

import { DeploymentMode } from '@/features/deployments';

import { MessageListFilter, SortValsTypes } from '../types';

export const messagingKeys = {
  listAll: (mode: DeploymentMode, name: string) => ['messaging', 'list', mode, name] as const,
  listSpecific: (
    filters: {
      mode: DeploymentMode;
      name: string;
      search_after_vals: SortValsTypes[];
    } & MessageListFilter
  ) => ['messaging', 'list', filters] as const,
};
