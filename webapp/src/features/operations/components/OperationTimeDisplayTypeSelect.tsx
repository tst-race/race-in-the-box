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

import { HTMLSelect } from '@blueprintjs/core';

import { OperationTimeDisplayType } from '../types';

// const options = ['relative', 'absolute'];
const options = [
  { label: 'Show relative time', value: 'relative' },
  { label: 'Show absolute time', value: 'absolute' },
];

export type OperationTimeDisplayTypeSelectProps = {
  displayType: OperationTimeDisplayType;
  setDisplayType: (displayType: OperationTimeDisplayType) => void;
};

export const OperationTimeDisplayTypeSelect = ({
  displayType,
  setDisplayType,
}: OperationTimeDisplayTypeSelectProps) => (
  <HTMLSelect
    onChange={(event) => setDisplayType(event.currentTarget.value as OperationTimeDisplayType)}
    options={options}
    value={displayType}
  />
);
