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

import { ProductTour } from '@/components/ProductTour';

const steps = [
  {
    target: '#name',
    disableBeacon: true,
    content: 'Specify a unique name for the deployment',
  },
  {
    target: '#race_core',
    content: 'Specify the source of the RACE core kits to be used for the deployment',
  },
  {
    target: '#network_manager_kit',
    content: 'Specify the source of the network manager plugin kit to be used in the deployment',
  },
  {
    target: '#comms_channels\\.0\\.value',
    content: 'Specify the comms channels to be enabled within the deployment',
  },
  {
    target: '#comms_channels-add',
    content: 'Add additional comms channels',
  },
  {
    target: '#comms_kits\\.0\\.value',
    content: 'Specify the sources of the comms plugin kits to be used in the deployment',
  },
  {
    target: '#comms_kits-add',
    content: 'Add additional comms plugin kits',
  },
  {
    target: '#nodes_and_enclaves',
    content: (
      <div>
        Define all the nodes that are in the deployment by:
        <br />
        <ol>
          <li>Creating node classes</li>
          <li>Creating enclave classes</li>
          <li>Creating enclave instances</li>
        </ol>
      </div>
    ),
  },
  {
    target: '.tl-node-classes',
    content: 'Parameters defining a particular class of node (e.g., Android phones, home servers)',
  },
  {
    target: '.tl-enclave-classes',
    content: 'Counts of node classes that are grouped together',
  },
  {
    target: '.tl-enclaves',
    content: 'Counts of enclave classes that make up the deployment',
  },
  {
    target: '#create_deployment',
    content: 'Once all parameters have been specified, click to create the deployment',
    showSkipButton: false,
  },
];

export const CreateLocalDeploymentTour = () => <ProductTour steps={steps} />;
