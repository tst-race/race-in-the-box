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

import { StateTransition } from './StateTransition';

export default {
  title: 'Features/StateVisualization/StateTransition',
  component: StateTransition,
} as ComponentMeta<typeof StateTransition>;

const Template: ComponentStory<typeof StateTransition> = (args) => <StateTransition {...args} />;

export const DefaultStyle = Template.bind({});
DefaultStyle.args = {
  name: 'Default',
};

export const Inverted = Template.bind({});
Inverted.args = {
  inverted: true,
  name: 'Inverted',
};

export const Reverse = Template.bind({});
Reverse.args = {
  name: 'Reverse',
  reverse: true,
};

/** Storybook sets a default action to the onClick prop */
export const NoOnClick = Template.bind({});
NoOnClick.args = {
  name: 'No On Click',
  onClick: undefined,
  width: 120,
};

export const Positioned = Template.bind({});
Positioned.args = {
  name: 'Positioned',
  height: 120,
  width: 200,
  xPos: 100,
  yPos: 200,
};
