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

import { ComponentStory, ComponentMeta } from '@storybook/react';
import { MemoryRouter } from 'react-router-dom';

import { QueuedOperation } from '../../types';

import { OperationListItem } from './OperationListItem';

export default {
  title: 'Features/Operations/OperationListItem',
  component: OperationListItem,
  decorators: [(story) => <MemoryRouter>{story()}</MemoryRouter>],
} as ComponentMeta<typeof OperationListItem>;

const baseOperation: QueuedOperation = {
  id: 1,
  name: 'Operation name',
  requestMethod: 'POST',
  requestPath: '',
  requestQuery: '',
  requestBody: '',
  postedTime: '2022-09-09T18:59:21.160940',
  target: 'deployment:local:deployment-name',
  state: 'PENDING',
  startedTime: null,
  stoppedTime: null,
};

const Template: ComponentStory<typeof OperationListItem> = (args) => (
  <OperationListItem {...args} />
);

export const Pending = Template.bind({});
Pending.args = {
  operation: baseOperation,
};

export const Invalid = Template.bind({});
Invalid.args = {
  operation: {
    ...baseOperation,
    state: 'INVALID',
  },
};

export const Cancelled = Template.bind({});
Cancelled.args = {
  operation: {
    ...baseOperation,
    state: 'CANCELLED',
  },
};

export const Running = Template.bind({});
Running.args = {
  operation: {
    ...baseOperation,
    state: 'RUNNING',
    startedTime: '2022-09-09T18:59:57.867539',
  },
};

export const Failed = Template.bind({});
Failed.args = {
  operation: {
    ...baseOperation,
    state: 'FAILED',
    startedTime: '2022-09-09T18:59:57.867539',
    stoppedTime: '2022-09-09T19:02:03.141592',
  },
};

export const Aborted = Template.bind({});
Aborted.args = {
  operation: {
    ...baseOperation,
    state: 'ABORTED',
    startedTime: '2022-09-09T18:59:57.867539',
    stoppedTime: '2022-09-09T20:05:03.141592',
  },
};

export const Succeeded = Template.bind({});
Succeeded.args = {
  operation: {
    ...baseOperation,
    state: 'SUCCEEDED',
    startedTime: '2022-09-09T18:59:57.867539',
    stoppedTime: '2022-09-09T19:17:03.141592',
  },
};
