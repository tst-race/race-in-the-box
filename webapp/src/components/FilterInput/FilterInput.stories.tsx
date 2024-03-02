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

import { FilterInput } from './FilterInput';

export default {
  title: 'Components/FilterInput',
  component: FilterInput,
} as ComponentMeta<typeof FilterInput>;

const Template: ComponentStory<typeof FilterInput> = (args) => <FilterInput {...args} />;

const filters = {
  type: { node: 'node', container: 'container' },
  state: { absent: 'not present', present: 'present' },
  healthy: { true: 'true', false: 'false' },
};

export const InitiallyEmpty = Template.bind({});
InitiallyEmpty.args = {
  availableFilters: filters,
  currentFilters: {},
};

export const InitialValues = Template.bind({});
InitialValues.args = {
  availableFilters: filters,
  currentFilters: {
    type: 'node',
    state: 'absent',
  },
};
