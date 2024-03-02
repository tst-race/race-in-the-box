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

import { Icon, IconProps } from '@blueprintjs/core';

import { formatDuration } from '@/utils/formatDuration';

import { OperationState } from '../../types';

import styles from './OperationDuration.module.css';

const stateToIconName: Record<OperationState, IconProps['icon']> = {
  PENDING: 'blank',
  CANCELLED: 'blank',
  RUNNING: 'stopwatch',
  SUCCEEDED: 'time',
  FAILED: 'time',
  ABORTED: 'time',
  INVALID: 'blank',
};

type OperationDurationProps = {
  startedTime: string | null;
  state: OperationState;
  stoppedTime: string | null;
};

export const OperationDuration = ({ startedTime, state, stoppedTime }: OperationDurationProps) => (
  <div className={styles.duration}>
    <Icon icon={stateToIconName[state]} size={12} />
    {state == 'RUNNING' && <span>In progress</span>}
    {startedTime && stoppedTime && <span>{formatDuration(startedTime, stoppedTime)}</span>}
  </div>
);
