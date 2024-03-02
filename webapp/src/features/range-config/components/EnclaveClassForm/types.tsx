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

import {
  EnclaveClassParams,
  NodeClassParams,
  NodeInstanceParams,
  PortMappingParams,
} from '../../types';

export type Inputs = EnclaveClassParams & {
  name: string;
  nodeClasses: Record<string, NodeClassParams>;
};

export const emptyEnclaveClass: Readonly<Inputs> = {
  name: '',
  nodes: [
    {
      nodeClassName: '',
      nodeQuantity: 1,
      portMapping: [],
    },
  ],
  nodeClasses: {},
};

export const emptyNodeInstance: Readonly<NodeInstanceParams> = {
  nodeClassName: '',
  nodeQuantity: 1,
  portMapping: [],
};

export const emptyPortMapping: Readonly<PortMappingParams> = {
  startExternalPort: 1024,
  internalPort: 1024,
};
