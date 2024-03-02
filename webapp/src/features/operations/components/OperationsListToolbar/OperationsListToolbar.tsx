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

import { ClearQueueButton } from '../ClearQueueButton';
import { OperationFilterInput, OperationFilterInputProps } from '../OperationFilterInput';
import {
  OperationTimeDisplayTypeSelect,
  OperationTimeDisplayTypeSelectProps,
} from '../OperationTimeDisplayTypeSelect';

import styles from './OperationsListToolbar.module.css';

type OperationsListToolbarProps = OperationFilterInputProps & OperationTimeDisplayTypeSelectProps;

export const OperationsListToolbar = ({
  displayType,
  filters,
  setDisplayType,
  setFilters,
}: OperationsListToolbarProps) => (
  <div className={styles.toolbar}>
    <OperationFilterInput filters={filters} setFilters={setFilters} />
    <OperationTimeDisplayTypeSelect displayType={displayType} setDisplayType={setDisplayType} />
    <ClearQueueButton />
  </div>
);
