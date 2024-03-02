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

import { ButtonProps } from '@blueprintjs/core';
import clsx from 'clsx';

import { NavButton, NavButtonProps } from '@/components/NavButton';

import { OperationState } from '../../types';

import styles from './OperationStatusButton.module.css';

const stateToClassName: Record<OperationState, string> = {
  PENDING: styles.pending,
  CANCELLED: styles.cancelled,
  RUNNING: styles.running,
  SUCCEEDED: styles.succeeded,
  FAILED: styles.failed,
  ABORTED: styles.aborted,
  INVALID: styles.invalid,
};

const stateToIconName: Record<OperationState, ButtonProps['icon']> = {
  PENDING: 'pause',
  CANCELLED: 'disable',
  RUNNING: 'ring',
  SUCCEEDED: 'tick-circle',
  FAILED: 'delete',
  ABORTED: 'ban-circle',
  INVALID: 'error',
};

type OperationStatusButtonProps = {
  state: OperationState;
  to: NavButtonProps['to'];
};

export const OperationStatusButton = ({ state, to }: OperationStatusButtonProps) => (
  <NavButton
    className={clsx(styles.operationStatusButton, stateToClassName[state])}
    icon={stateToIconName[state]}
    text={state.toLowerCase()}
    to={to}
  />
);
