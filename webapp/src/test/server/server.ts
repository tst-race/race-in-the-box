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

import { DefaultBodyType, PathParams, ResponseResolver, rest, RestContext, RestRequest } from 'msw';
import { setupServer } from 'msw/node';

import { handlers } from './handlers';

const server = setupServer(...handlers);

const verifyPayload =
  <T extends Record<string, any>>(
    expected: T
  ): ResponseResolver<
    RestRequest<DefaultBodyType, PathParams<string>>,
    RestContext,
    DefaultBodyType
  > =>
  async (req, res, ctx) => {
    const payload: T = (await req.json()) as T;
    for (const keyName of Object.keys(expected)) {
      if (expected[keyName] != payload[keyName]) {
        return res(
          ctx.text(`Expected ${keyName} ${expected[keyName]} does not match ${payload[keyName]}`),
          ctx.status(400)
        );
      }
      return res(ctx.status(200));
    }
  };

export { rest, server, verifyPayload };
