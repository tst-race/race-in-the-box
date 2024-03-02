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

import { action } from '@storybook/addon-actions';
import { ComponentStory, ComponentMeta } from '@storybook/react';

import { Pagination } from './Pagination';

export default {
  title: 'Components/Pagination',
  component: Pagination,
} as ComponentMeta<typeof Pagination>;

const Template: ComponentStory<typeof Pagination> = (args) => <Pagination {...args} />;

export const NoPages = Template.bind({});
NoPages.args = {
  page: 1,
  setPage: action('setPage'),
  size: 20,
  total: 0,
};

export const FewPages = Template.bind({});
FewPages.args = {
  page: 2,
  setPage: action('setPage'),
  size: 10,
  total: 46,
};

export const MaxBeforeSkipping = Template.bind({});
MaxBeforeSkipping.args = {
  page: 7,
  setPage: action('setPage'),
  size: 10,
  total: 92,
};

export const MiddleOfMany = Template.bind({});
MiddleOfMany.args = {
  page: 22,
  setPage: action('setPage'),
  size: 10,
  total: 462,
};

export const LessPadding = Template.bind({});
LessPadding.args = {
  ...MiddleOfMany.args,
  pad: 2,
};
