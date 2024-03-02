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

import { RangeConfig } from './index';

loadApiSpec();

test('RangeConfig matches spec', () => {
  const payload: RangeConfig = {
    range: {
      name: faker.datatype.string(),
      bastion: {
        range_ip: '',
      },
      RACE_nodes: [
        {
          name: faker.datatype.string(),
          type: 'client',
          enclave: faker.datatype.string(),
          nat: faker.datatype.boolean(),
          identities: [],
          genesis: faker.datatype.boolean(),
          gpu: faker.datatype.boolean(),
          bridge: faker.datatype.boolean(),
          platform: 'android',
          architecture: 'arm64-v8a',
          environment: 'phone',
        },
      ],
      enclaves: [
        {
          name: faker.datatype.string(),
          ip: faker.internet.ipv4(),
          hosts: [faker.internet.domainName()],
          port_mapping: {
            '*': {
              hosts: [faker.internet.domainName()],
              port: '*',
            },
          },
        },
      ],
      services: [
        {
          name: faker.datatype.string(),
          access: [
            {
              protocol: faker.internet.protocol(),
              url: faker.internet.url(),
              userFmt: faker.datatype.string(),
              password: faker.internet.password(),
            },
          ],
          type: faker.datatype.string(),
          'auth-req-view': faker.datatype.string(),
          'auth-req-reply': faker.datatype.string(),
          'auth-req-post': faker.datatype.string(),
          'auth-req_delete': faker.datatype.string(),
        },
      ],
    },
  };
  expect(payload).toSatisfySchemaInApiSpec('RangeConfig');
});
