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

import { StateColor } from '@/features/state-visualization';

import { NodeStatus } from '../types';

export const NodeStatusColors: Record<NodeStatus, StateColor> = {
  READY_TO_GENERATE_CONFIG: 'gold',
  READY_TO_TAR_CONFIGS: 'sepia',
  DOWN: 'gray',
  READY_TO_PUBLISH_CONFIGS: 'violet',
  READY_TO_INSTALL_CONFIGS: 'indigo',
  READY_TO_BOOTSTRAP: 'blue',
  READY_TO_START: 'cerulean',
  INITIALIZING: 'lime',
  RUNNING: 'green',
  STOPPED: 'turquoise',
  ERROR: 'red',
  UNKNOWN: 'orange',
};
