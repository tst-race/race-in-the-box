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

import { OperationLogs, OperationsQueuePage, QueuedOperation } from '@/features/operations';
import { OperationQueuedResult } from '@/types';

const queuedOperation: QueuedOperation = {
  id: 3,
  name: 'Operation name 3',
  requestMethod: 'POST',
  requestPath: '/api/demo',
  requestQuery: '',
  requestBody: '{"key": "value"}',
  postedTime: '2022-09-09T18:59:21.160940',
  target: 'deployment:local:local-deployment-a',
  state: 'RUNNING',
  startedTime: '2022-09-09T19:00:06.762362',
  stoppedTime: null,
};

const operationsQueuePage1: OperationsQueuePage = {
  operations: [
    {
      id: 4,
      name: 'Operation name 4',
      requestMethod: 'PUT',
      requestPath: '/api/demo/params',
      requestQuery: '',
      requestBody: '{"key": "value"}',
      postedTime: '2022-09-09T19:02:17.160940',
      target: 'deployment:local:local-deployment-b',
      state: 'PENDING',
      startedTime: null,
      stoppedTime: null,
    },
    queuedOperation,
  ],
  page: 1,
  size: 20,
  total: 24,
};

const operationsQueuePage2: OperationsQueuePage = {
  operations: [
    {
      id: 2,
      name: 'Operation name 2',
      requestMethod: 'POST',
      requestPath: '/api/demo',
      requestQuery: '',
      requestBody: '{"key": "different value"}',
      postedTime: '2022-09-09T18:42:21.160940',
      target: 'deployment:local:local-deployment-b',
      state: 'FAILED',
      startedTime: '2022-09-09T18:42:25.762362',
      stoppedTime: '2022-09-09T18:42:55.144322',
    },
    {
      id: 1,
      name: 'Operation name 1',
      requestMethod: 'POST',
      requestPath: '/api/demo/operation',
      requestQuery: '',
      requestBody: '',
      postedTime: '2022-09-09T18:02:21.160940',
      target: 'deployment:local:local-deployment-c',
      state: 'SUCCEEDED',
      startedTime: '2022-09-09T18:02:25.762362',
      stoppedTime: '2022-09-09T18:39:55.144322',
    },
  ],
  page: 2,
  size: 20,
  total: 24,
};

const operationsQueuePageAll: OperationsQueuePage = {
  operations: [...operationsQueuePage1.operations, ...operationsQueuePage2.operations],
  page: 1,
  size: 30,
  total: 24,
};

const operationLogsPage1: OperationLogs = {
  lines: [
    {
      source: 'LOG',
      logLevel: 'INFO',
      text: 'Starting operation...',
      time: '2022-09-09T19:00:14.123456',
    },
    {
      source: 'LOG',
      logLevel: 'DEBUG',
      text: 'key was "value"',
      time: '2022-09-09T19:00:14.234567',
    },
    {
      source: 'STDOUT',
      logLevel: 'INFO',
      text: "oops this didn't use a logger",
      time: '2022-09-09T19:00:31.123456',
    },
    {
      source: 'LOG',
      logLevel: 'WARNING',
      text: 'some kind of warning',
      time: '2022-09-09T19:00:42.424242',
    },
  ],
  offset: 0,
  limit: 1000,
  total: 1200,
};

const operationLogsPage2: OperationLogs = {
  lines: [
    {
      source: 'LOG',
      logLevel: 'ERROR',
      text: 'ruh-roh!!',
      time: '2022-09-09T19:01:03.123456',
    },
    {
      source: 'LOG',
      logLevel: 'INFO',
      text: 'Completed operation',
      time: '2022-09-09T19:01:23.123456',
    },
  ],
  offset: 1000,
  limit: 1000,
  total: 1200,
};

const operationQueuedResult: OperationQueuedResult = {
  id: 5,
};

export const operationHandlers = [
  rest.get('/api/operations', (req, res, ctx) => {
    if (req.url.searchParams.get('size') == '30') {
      return res(ctx.json(operationsQueuePageAll), ctx.delay(1500));
    } else if (req.url.searchParams.get('page') == '1') {
      return res(ctx.json(operationsQueuePage1), ctx.delay(1500));
    }
    return res(ctx.json(operationsQueuePage2), ctx.delay(2000));
  }),
  rest.get(/\/api\/operations\/\d+\/logs/, (req, res, ctx) => {
    if (req.url.searchParams.get('offset') == '0') {
      return res(ctx.json(operationLogsPage1), ctx.delay(1500));
    }
    return res(ctx.json(operationLogsPage2), ctx.delay(2000));
  }),
  rest.put(/\/api\/operations\/\d+\/state/, (req, res, ctx) => res(ctx.status(200))),
  rest.post(/\/api\/operations\/\d+\/retry/, (req, res, ctx) =>
    res(ctx.json(operationQueuedResult), ctx.status(201))
  ),
  rest.get(/\/api\/operations\/\d+/, (req, res, ctx) =>
    res(ctx.json(queuedOperation), ctx.delay(500))
  ),
];
