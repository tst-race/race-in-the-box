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

import { OperationLogs, OperationsQueuePage, QueuedOperation } from './index';

loadApiSpec();

test('QueuedOperation matches spec', () => {
  const payload: QueuedOperation = {
    id: faker.datatype.number(),
    name: faker.datatype.string(),
    requestMethod: 'POST',
    requestPath: faker.internet.url(),
    requestQuery: faker.datatype.string(),
    requestBody: faker.datatype.json(),
    postedTime: faker.datatype.datetime().toISOString(),
    target: faker.datatype.string(),
    state: 'RUNNING',
    startedTime: faker.datatype.datetime().toISOString(),
    stoppedTime: null,
  };
  expect(payload).toSatisfySchemaInApiSpec('QueuedOperation');
});

test('OperationsQueuePage matches spec', () => {
  const payload: OperationsQueuePage = {
    operations: [],
    page: faker.datatype.number(),
    size: faker.datatype.number(),
    total: faker.datatype.number(),
  };
  expect(payload).toSatisfySchemaInApiSpec('OperationsQueuePage');
});

test('OperationLogs matches spec', () => {
  const payload: OperationLogs = {
    lines: [
      {
        source: 'LOG',
        logLevel: 'INFO',
        text: faker.datatype.string(),
        time: faker.datatype.datetime().toISOString(),
      },
    ],
    offset: faker.datatype.number(),
    limit: faker.datatype.number(),
    total: faker.datatype.number(),
  };
  expect(payload).toSatisfySchemaInApiSpec('OperationLogs');
});
