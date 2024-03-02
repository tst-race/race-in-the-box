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

import { faker } from '@faker-js/faker';

import { loadApiSpec } from '@/test/openApiSpec';

import {
  EnclaveClassTemplate,
  EnclaveClassTemplateList,
  EnclaveInstanceTemplate,
  EnclaveInstanceTemplateList,
  NodeClassTemplate,
  NodeClassTemplateList,
} from '.';

loadApiSpec();

test('NodeClassTemplate matches spec', () => {
  const payload: NodeClassTemplate = {
    name: faker.datatype.string(),
    type: 'client',
    nat: faker.datatype.boolean(),
    genesis: faker.datatype.boolean(),
    gpu: faker.datatype.boolean(),
    bridge: faker.datatype.boolean(),
    platform: 'android',
    architecture: 'arm64-v8a',
    environment: faker.datatype.string(),
  };
  expect(payload).toSatisfySchemaInApiSpec('NodeClassTemplate');
});

test('NodeClassTemplateList matches spec', () => {
  const payload: NodeClassTemplateList = {
    nodeClasses: [faker.datatype.string()],
  };
  expect(payload).toSatisfySchemaInApiSpec('NodeClassTemplateList');
});

test('EnclaveClassTemplate matches spec', () => {
  const payload: EnclaveClassTemplate = {
    name: faker.datatype.string(),
    nodes: [
      {
        nodeClassName: faker.datatype.string(),
        nodeQuantity: faker.datatype.number(),
        portMapping: [
          {
            startExternalPort: faker.datatype.number(),
            internalPort: faker.datatype.number(),
          },
        ],
      },
    ],
  };
  expect(payload).toSatisfySchemaInApiSpec('EnclaveClassTemplate');
});

test('EnclaveClassTemplateList matches spec', () => {
  const payload: EnclaveClassTemplateList = {
    enclaveClasses: [faker.datatype.string()],
  };
  expect(payload).toSatisfySchemaInApiSpec('EnclaveClassTemplateList');
});

test('EnclaveInstanceTemplate matches spec', () => {
  const payload: EnclaveInstanceTemplate = {
    name: faker.datatype.string(),
    enclaveClassName: faker.datatype.string(),
    enclaveQuantity: faker.datatype.number(),
  };
  expect(payload).toSatisfySchemaInApiSpec('EnclaveInstanceTemplate');
});

test('EnclaveInstanceTemplateList matches spec', () => {
  const payload: EnclaveInstanceTemplateList = {
    enclaveInstances: [faker.datatype.string()],
  };
  expect(payload).toSatisfySchemaInApiSpec('EnclaveInstanceTemplateList');
});
