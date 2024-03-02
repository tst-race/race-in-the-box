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

import { StateTag } from './StateTag';

export default {
  title: 'Features/StateVisualization/StateTag',
  component: StateTag,
} as ComponentMeta<typeof StateTag>;

const Template: ComponentStory<typeof StateTag> = (args) => <StateTag {...args} />;

export const DefaultStyle = Template.bind({});
DefaultStyle.args = {
  children: 'Text',
};

export const Disabled = Template.bind({});
Disabled.args = {
  disabled: true,
  children: 'Disabled',
};
