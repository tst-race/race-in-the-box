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

import { StateBox } from './StateBox';

export default {
  title: 'Features/StateVisualization/StateBox',
  component: StateBox,
} as ComponentMeta<typeof StateBox>;

const Template: ComponentStory<typeof StateBox> = (args) => <StateBox {...args} />;

export const DefaultStyle = Template.bind({});
DefaultStyle.args = {
  name: 'Default',
};

export const MultiWordName = Template.bind({});
MultiWordName.args = {
  name: 'Ready to Generate Configs',
};

export const Disabled = Template.bind({});
Disabled.args = {
  disabled: true,
  name: 'Disabled',
};

export const Positioned = Template.bind({});
Positioned.args = {
  name: 'Positioned',
  xPos: 200,
  yPos: 100,
};
