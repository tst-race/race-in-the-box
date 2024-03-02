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

export type OperationState =
  | 'PENDING'
  | 'CANCELLED'
  | 'RUNNING'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'ABORTED'
  | 'INVALID';

export type QueuedOperation = {
  id: number;
  name: string;
  requestMethod: 'GET' | 'PUT' | 'PATCH' | 'POST' | 'DELETE';
  requestPath: string;
  requestQuery: string;
  requestBody: string;
  postedTime: string;
  target: string;
  state: OperationState;
  startedTime: string | null;
  stoppedTime: string | null;
};

export type OperationsQueuePage = {
  operations: QueuedOperation[];
  page: number;
  size: number;
  total: number;
};

export type LogLevel = 'CRITICAL' | 'ERROR' | 'WARNING' | 'INFO' | 'DEBUG' | 'TRACE' | 'NOTSET';

export type OperationOutputLine = {
  source: 'STDOUT' | 'STDERR' | 'LOG';
  logLevel: LogLevel;
  text: string;
  time: string;
};

export type OperationLogs = {
  lines: OperationOutputLine[];
  offset: number;
  limit: number;
  total: number;
};

export type LiveOperationLogsUpdate = {
  lines: OperationOutputLine[];
};

export type OperationStateUpdate = {
  id: number;
  name: string;
  state: OperationState;
};

export type OperationFilter = {
  targetType: string;
  targetName: string;
};

export type OperationTimeDisplayType = 'absolute' | 'relative';
