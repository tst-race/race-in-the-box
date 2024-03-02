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

import { ComponentMeta } from '@storybook/react';

import { StateBox } from '../StateBox';
import { StateTransition } from '../StateTransition';

import { StateVisualizationCanvas } from './StateVisualizationCanvas';

export default {
  title: 'Features/StateVisualization/StateVisualizationCanvas',
  component: StateVisualizationCanvas,
} as ComponentMeta<typeof StateVisualizationCanvas>;

export const JustStates = () => (
  <StateVisualizationCanvas>
    <StateBox name="Initial State" xPos={0} yPos={50} />
    <StateBox name="Next State" xPos={90} yPos={50} />
    <StateBox name="Final State" xPos={180} yPos={50} />
  </StateVisualizationCanvas>
);

export const SimpleTransitions = () => (
  <StateVisualizationCanvas>
    <StateBox name="Initial State" xPos={0} yPos={50} />
    <StateBox name="Next State" xPos={90} yPos={50} />
    <StateBox name="Final State" xPos={180} yPos={50} />
    <StateTransition name="Start" width={90} xPos={20} />
    <StateTransition inverted name="Stop" reverse width={180} xPos={55} yPos={125} />
  </StateVisualizationCanvas>
);

export const ComplexTransitions = () => (
  <StateVisualizationCanvas>
    <StateBox name="Initial State" xPos={0} yPos={60} />
    <StateBox name="Next State" xPos={90} yPos={60} />
    <StateBox name="Final State" xPos={180} yPos={60} />
    <StateTransition name="Go to Final" height={60} width={180} xPos={20} />
    <StateTransition name="Start" height={25} width={90} xPos={40} yPos={35} />
    <StateTransition inverted name="Stop" reverse height={25} width={90} xPos={125} yPos={135} />
    <StateTransition
      inverted
      name="Go to Initial"
      reverse
      height={60}
      width={180}
      xPos={55}
      yPos={135}
    />
  </StateVisualizationCanvas>
);
