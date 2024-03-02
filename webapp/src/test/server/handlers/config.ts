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

import { rest } from 'msw';

import { RibInfo } from '@/features/config';

const ribInfo: RibInfo = {
  version: 'stub-version',
  image_tag: 'stub-image-tag',
  image_digest: 'stub-image-digest',
  image_created: 'stub-image-created',
};

export const configHandlers = [rest.get('/api/info', (req, res, ctx) => res(ctx.json(ribInfo)))];
