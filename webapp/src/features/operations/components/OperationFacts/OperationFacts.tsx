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

import { Divider, H4, Text } from '@blueprintjs/core';

import { QueuedOperation } from '../../types';
import { OperationActions } from '../OperationActions';
import { OperationDuration } from '../OperationDuration';
import { OperationStatusButton } from '../OperationStatusButton';
import { OperationStopped } from '../OperationStopped';
import { OperationTarget } from '../OperationTarget';
import { RequestFactsButton } from '../RequestFactsButton';

import styles from './OperationFacts.module.css';

type OperationFactsProps = {
  operation: QueuedOperation;
};

export const OperationFacts = ({ operation }: OperationFactsProps) => (
  <>
    <H4>
      <Text ellipsize>{operation.name}</Text>
    </H4>
    <Divider />
    <div className={styles.widgets}>
      <div>
        <OperationStatusButton state={operation.state} to="." />
        <OperationDuration
          startedTime={operation.startedTime}
          state={operation.state}
          stoppedTime={operation.stoppedTime}
        />
        <OperationStopped stoppedTime={operation.stoppedTime} />
      </div>
      <div>
        <OperationActions id={operation.id} name={operation.name} state={operation.state} />
      </div>
    </div>
    <Divider />
    <div>
      <b>Target:</b>
      <OperationTarget target={operation.target} />
    </div>
    <Divider />
    <div>
      <b>Created:</b>
      <Text ellipsize>{operation.postedTime}</Text>
    </div>
    <div>
      <b>Request:</b>
      <RequestFactsButton
        requestMethod={operation.requestMethod}
        requestPath={operation.requestPath}
        requestQuery={operation.requestQuery}
        requestBody={operation.requestBody}
      />
    </div>
    {operation.startedTime && (
      <div>
        <b>Started:</b>
        <Text ellipsize>{operation.startedTime}</Text>
      </div>
    )}
    {operation.stoppedTime && (
      <div>
        <b>Stopped:</b>
        <Text ellipsize>{operation.stoppedTime}</Text>
      </div>
    )}
  </>
);
