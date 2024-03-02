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

export const operationKeys = {
  all: ['operations'] as const,
  page: (page: number, size: number, target?: string) =>
    [...operationKeys.all, 'page', { page, size, target }] as const,
  detail: (id: number) => [...operationKeys.all, 'detail', id] as const,
  logs: (id: number, offset: number, limit: number) =>
    [...operationKeys.all, 'logs', id, { offset, limit }] as const,
};
