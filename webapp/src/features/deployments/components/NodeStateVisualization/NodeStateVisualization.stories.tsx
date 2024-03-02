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

import { ComponentMeta, ComponentStory } from '@storybook/react';

import { NodeStateVisualization } from './NodeStateVisualization';

export default {
  title: 'Features/Deployments/NodeStateVisualization',
  component: NodeStateVisualization,
} as ComponentMeta<typeof NodeStateVisualization>;

const Template: ComponentStory<typeof NodeStateVisualization> = (args) => (
  <NodeStateVisualization {...args} />
);

export const Genesis = Template.bind({});
Genesis.args = {
  allStatuses: [],
  canBootstrap: false,
  numSelected: 1,
};

export const NonGenesis = Template.bind({});
NonGenesis.args = {
  allStatuses: [],
  canBootstrap: true,
  numSelected: 1,
};

export const Force = Template.bind({});
Force.args = {
  allStatuses: ['RUNNING'],
  canBootstrap: false,
  force: true,
  numSelected: 1,
};
