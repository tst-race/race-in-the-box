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

import { Divider } from '@blueprintjs/core';
import clsx from 'clsx';

import { OperationTimeDisplayType, QueuedOperation } from '../../types';
import { OperationActions } from '../OperationActions';
import { OperationDuration } from '../OperationDuration';
import { OperationStatusButton } from '../OperationStatusButton';
import { OperationStopped } from '../OperationStopped';

import styles from './OperationListItem.module.css';

export type OperationListItemProps = {
  displayType: OperationTimeDisplayType;
  operation: QueuedOperation;
};

export const OperationListItem = ({ displayType, operation }: OperationListItemProps) => (
  <>
    <Divider className={styles.divider} />
    <div
      className={clsx(styles.operationListItem, { [styles.absolute]: displayType == 'absolute' })}
    >
      <div>
        <OperationStatusButton state={operation.state} to={`${operation.id}`} />
        <OperationDuration
          startedTime={operation.startedTime}
          state={operation.state}
          stoppedTime={operation.stoppedTime}
        />
        <OperationStopped displayType={displayType} stoppedTime={operation.stoppedTime} />
      </div>
      <span>
        #{operation.id} {operation.name}
      </span>
      <span>
        <OperationActions id={operation.id} name={operation.name} state={operation.state} />
      </span>
    </div>
  </>
);
