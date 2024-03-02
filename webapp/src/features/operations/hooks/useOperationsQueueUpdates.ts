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

import { Intent } from '@blueprintjs/core';
import useWebSocket from 'react-use-websocket';

import { queryClient } from '@/lib/react-query';
import { getToaster } from '@/lib/toaster';

import { operationKeys } from '../api/queryKeys';
import { OperationState, OperationStateUpdate } from '../types';

const stateToMessage: Record<OperationState, string> = {
  PENDING: 'has been added to the queue',
  CANCELLED: 'has been cancelled',
  RUNNING: 'is running',
  SUCCEEDED: 'has successfully completed',
  FAILED: 'resulted in a failure',
  ABORTED: 'has been aborted',
  INVALID: 'is not valid',
};

const stateToIntent: Record<OperationState, Intent> = {
  PENDING: Intent.NONE,
  CANCELLED: Intent.NONE,
  RUNNING: Intent.PRIMARY,
  SUCCEEDED: Intent.SUCCESS,
  FAILED: Intent.DANGER,
  ABORTED: Intent.WARNING,
  INVALID: Intent.DANGER,
};

export const useOperationsQueueUpdates = () =>
  useWebSocket(`ws://${window.location.host}/api/operations/ws`, {
    onMessage: (event) => {
      const update: OperationStateUpdate = JSON.parse(event.data);
      queryClient.invalidateQueries(operationKeys.all);
      queryClient.invalidateQueries(['deployments']);
      getToaster().show({
        message: `Operation #${update.id}, ${update.name}, ${stateToMessage[update.state]}`,
        intent: stateToIntent[update.state],
      });
    },
    shouldReconnect: () => true,
  });
