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

import { rest } from 'msw';

import {
  EnclaveClassTemplate,
  EnclaveClassTemplateList,
  EnclaveInstanceTemplate,
  EnclaveInstanceTemplateList,
  NodeClassTemplate,
  NodeClassTemplateList,
} from '@/features/templates';

const nodeClassTemplates: NodeClassTemplateList = {
  nodeClasses: ['node-class-a', 'node-class-b'],
};

const nodeClassTemplate: NodeClassTemplate = {
  name: 'node class template',
  architecture: 'auto',
  bridge: true,
  environment: 'phone',
  genesis: false,
  gpu: false,
  nat: false,
  platform: 'android',
  type: 'client',
};

const enclaveClassTemplates: EnclaveClassTemplateList = {
  enclaveClasses: ['enclave-class-a', 'enclave-class-b'],
};

const enclaveClassTemplate: EnclaveClassTemplate = {
  name: 'enclave class template',
  nodes: [
    {
      nodeClassName: 'node-class-a',
      nodeQuantity: 6,
      portMapping: [],
    },
    {
      nodeClassName: 'node-class-b',
      nodeQuantity: 4,
      portMapping: [{ startExternalPort: 8000, internalPort: 80 }],
    },
  ],
};

const enclaveInstanceTemplates: EnclaveInstanceTemplateList = {
  enclaveInstances: ['enclave-instance-a', 'enclave-instance-b'],
};

const enclaveInstanceTemplate: EnclaveInstanceTemplate = {
  name: 'enclave instance template',
  enclaveClassName: 'enclave-class-a',
  enclaveQuantity: 2,
};

export const templateHandlers = [
  // Node class templates
  rest.get('/api/templates/node-classes', (req, res, ctx) => res(ctx.json(nodeClassTemplates))),
  rest.post('/api/templates/node-classes', (req, res, ctx) => res(ctx.status(201))),
  rest.get(/\/api\/templates\/node-classes\/.*/, (req, res, ctx) =>
    res(ctx.json(nodeClassTemplate))
  ),
  rest.put(/\/api\/templates\/node-classes\/.*/, (req, res, ctx) => res(ctx.status(200))),
  rest.delete(/\/api\/templates\/node-classes\/.*/, (req, res, ctx) => res(ctx.status(204))),
  // Enclave class templates
  rest.get('/api/templates/enclave-classes', (req, res, ctx) =>
    res(ctx.json(enclaveClassTemplates))
  ),
  rest.post('/api/templates/enclave-classes', (req, res, ctx) => res(ctx.status(201))),
  rest.get(/\/api\/templates\/enclave-classes\/.*/, (req, res, ctx) =>
    res(ctx.json(enclaveClassTemplate))
  ),
  rest.put(/\/api\/templates\/enclave-classes\/.*/, (req, res, ctx) => res(ctx.status(200))),
  rest.delete(/\/api\/templates\/enclave-classes\/.*/, (req, res, ctx) => res(ctx.status(204))),
  // Enclave instance templates
  rest.get('/api/templates/enclave-instances', (req, res, ctx) =>
    res(ctx.json(enclaveInstanceTemplates))
  ),
  rest.post('/api/templates/enclave-instances', (req, res, ctx) => res(ctx.status(201))),
  rest.get(/\/api\/templates\/enclave-instances\/.*/, (req, res, ctx) =>
    res(ctx.json(enclaveInstanceTemplate))
  ),
  rest.put(/\/api\/templates\/enclave-instances\/.*/, (req, res, ctx) => res(ctx.status(200))),
  rest.delete(/\/api\/templates\/enclave-instances\/.*/, (req, res, ctx) => res(ctx.status(204))),
];
