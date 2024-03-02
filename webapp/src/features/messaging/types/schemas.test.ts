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

import { faker } from '@faker-js/faker';

import { loadApiSpec } from '@/test/openApiSpec';

import { SendAutoRequest, SendManualRequest } from './index';

loadApiSpec();

test('SendAutoRequest matches spec', () => {
  const payload: SendAutoRequest = {
    message_period: faker.datatype.number(),
    message_quantity: faker.datatype.number(),
    message_size: faker.datatype.number(),
    recipient: faker.datatype.string(),
    sender: faker.datatype.string(),
    test_id: faker.datatype.string(),
    network_manager_bypass_route: faker.datatype.string(),
    verify: faker.datatype.boolean(),
    timeout: faker.datatype.number(),
  };
  expect(payload).toSatisfySchemaInApiSpec('MessageSendAutoParams');
});

test('SendManualRequest matches spec', () => {
  const payload: SendManualRequest = {
    message_content: faker.datatype.string(),
    recipient: faker.datatype.string(),
    sender: faker.datatype.string(),
    test_id: faker.datatype.string(),
    network_manager_bypass_route: faker.datatype.string(),
    verify: faker.datatype.boolean(),
    timeout: faker.datatype.number(),
  };
  expect(payload).toSatisfySchemaInApiSpec('MessageSendManualParams');
});
