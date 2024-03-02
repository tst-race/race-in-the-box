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

import { RequestFacts } from './RequestFacts';

export default {
  title: 'Features/Operations/RequestFacts',
  component: RequestFacts,
} as ComponentMeta<typeof RequestFacts>;

const Template: ComponentStory<typeof RequestFacts> = (args) => <RequestFacts {...args} />;

export const NoQueryNoBody = Template.bind({});
NoQueryNoBody.args = {
  requestMethod: 'POST',
  requestPath: '/api/things',
  requestQuery: '',
  requestBody: '',
};

export const ShortQuery = Template.bind({});
ShortQuery.args = {
  requestMethod: 'DELETE',
  requestPath: '/api/things-to-delete',
  requestQuery: '?filter-key=filter-val&other-key=other-val',
  requestBody: '',
};

export const LongQuery = Template.bind({});
LongQuery.args = {
  requestMethod: 'GET',
  requestPath: '/api/fetchables',
  requestQuery:
    '?filter-key=filter-val&other-key=other-val&sort-order=asc&sort-key=field-name&include-children=yes&limit=100&offset=2200',
  requestBody: '',
};

export const ScalarBody = Template.bind({});
ScalarBody.args = {
  requestMethod: 'PUT',
  requestPath: '/api/things/1/prop',
  requestQuery: '',
  requestBody: '"value"',
};

export const ArrayBody = Template.bind({});
ArrayBody.args = {
  requestMethod: 'POST',
  requestPath: '/api/things',
  requestQuery: '',
  requestBody: '[true, 42, "str"]',
};

export const ObjectBody = Template.bind({});
ObjectBody.args = {
  requestMethod: 'POST',
  requestPath: '/api/complicated-objects',
  requestQuery: '',
  requestBody:
    '{"name":"a name","age":42,"retired":false,"children":[{"name":"child name","age":13},{"name":"other child name","age":11}]}',
};
