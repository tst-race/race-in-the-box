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

import { faker } from '@faker-js/faker';
import { action } from '@storybook/addon-actions';
import { ComponentStory, ComponentMeta } from '@storybook/react';
import { MemoryRouter } from 'react-router-dom';

import { LogWindow } from './LogWindow';

export default {
  title: 'Features/Operations/LogWindow',
  component: LogWindow,
  decorators: [(story) => <MemoryRouter>{story()}</MemoryRouter>],
} as ComponentMeta<typeof LogWindow>;

const Template: ComponentStory<typeof LogWindow> = (args) => <LogWindow {...args} />;

export const NoLogs = Template.bind({});
NoLogs.args = {
  limit: 1000,
  lines: [],
  offset: 0,
  setWindow: action('setWindow'),
  total: 0,
};

export const FewLogs = Template.bind({});
FewLogs.args = {
  limit: 1000,
  lines: [
    {
      source: 'STDOUT',
      logLevel: 'INFO',
      text: 'This is a line from stdout',
      time: '2022-09-13T10:03:22.123456',
    },
    {
      source: 'STDERR',
      logLevel: 'ERROR',
      text: 'This is a line from stderr',
      time: '2022-09-13T10:03:23.123456',
    },
    {
      source: 'LOG',
      logLevel: 'CRITICAL',
      text: 'This is a critical log line',
      time: '2022-09-13T10:03:24.123456',
    },
    {
      source: 'LOG',
      logLevel: 'ERROR',
      text: 'This is an error log line',
      time: '2022-09-13T10:03:25.123456',
    },
    {
      source: 'LOG',
      logLevel: 'WARNING',
      text: 'This is a warning log line',
      time: '2022-09-13T10:03:26.123456',
    },
    {
      source: 'LOG',
      logLevel: 'INFO',
      text: 'This is an info log line',
      time: '2022-09-13T10:03:27.123456',
    },
    {
      source: 'LOG',
      logLevel: 'DEBUG',
      text: 'This is a debug log line',
      time: '2022-09-13T10:03:28.123456',
    },
    {
      source: 'LOG',
      logLevel: 'TRACE',
      text: 'This is a trace log line',
      time: '2022-09-13T10:03:29.123456',
    },
    {
      source: 'LOG',
      logLevel: 'NOTSET',
      text: 'This is a notset log line',
      time: '2022-09-13T10:03:30.123456',
    },
  ],
  offset: 0,
  setWindow: action('setWindow'),
  total: 9,
};

export const LongLine = Template.bind({});
LongLine.args = {
  limit: 1000,
  lines: [
    {
      source: 'STDOUT',
      logLevel: 'INFO',
      text: faker.lorem.sentence(100),
      time: '2022-09-13T10:03:30.123456',
    },
    {
      source: 'STDOUT',
      logLevel: 'INFO',
      text: faker.lorem.sentence(10),
      time: '2022-09-13T10:03:30.123456',
    },
  ],
  offset: 0,
  setWindow: action('setWindow'),
  total: 2,
};

export const MultiLine = Template.bind({});
MultiLine.args = {
  limit: 1000,
  lines: [
    {
      source: 'LOG',
      logLevel: 'DEBUG',
      text: faker.lorem.lines(4),
      time: '2022-09-13T10:03:30.123456',
    },
    {
      source: 'STDOUT',
      logLevel: 'INFO',
      text: faker.lorem.lines(2),
      time: '2022-09-13T10:03:30.123456',
    },
  ],
  offset: 0,
  setWindow: action('setWindow'),
  total: 2,
};

export const HasNext = Template.bind({});
HasNext.args = {
  limit: 100,
  lines: [
    {
      source: 'STDOUT',
      logLevel: 'INFO',
      text: faker.lorem.sentence(),
      time: '2022-09-13T10:03:30.123456',
    },
    {
      source: 'STDOUT',
      logLevel: 'INFO',
      text: faker.lorem.sentence(),
      time: '2022-09-13T10:03:30.123456',
    },
  ],
  offset: 0,
  setWindow: action('setWindow'),
  total: 101,
};

export const HasPrev = Template.bind({});
HasPrev.args = {
  limit: 100,
  lines: HasNext.args.lines,
  offset: 40,
  setWindow: action('setWindow'),
  total: 70,
};

export const HasPrevAndNext = Template.bind({});
HasPrevAndNext.args = {
  limit: 100,
  lines: HasNext.args.lines,
  offset: 40,
  setWindow: action('setWindow'),
  total: 141,
};

export const HasFirstAndLast = Template.bind({});
HasFirstAndLast.args = {
  limit: 100,
  lines: HasNext.args.lines,
  offset: 100,
  setWindow: action('setWindow'),
  total: 251,
};
