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
  EnclaveInstanceParams,
  NodeClassParams,
  PortMapping,
  RangeConfig,
} from '../types';

export const generateRangeConfig = (
  nodeClasses: Record<string, NodeClassParams>,
  enclaveClasses: Record<string, EnclaveClassParams>,
  enclaves: EnclaveInstanceParams[]
): RangeConfig => {
  const rangeConfig: RangeConfig = {
    range: {
      name: '',
      bastion: { range_ip: '' },
      RACE_nodes: [],
      enclaves: [],
      services: [],
    },
  };

  const nodeCountByType = { client: 0, server: 0 };
  const enclaveCountByName: Record<string, number> = {};

  // For each enclave instance group...
  for (const enclave of enclaves) {
    if (!(enclave.enclaveClassName in enclaveCountByName)) {
      enclaveCountByName[enclave.enclaveClassName] = 0;
    }

    const enclaveClass = enclaveClasses[enclave.enclaveClassName];

    // ...create instances of the enclave class of the desired quantity
    for (let enclaveCount = 0; enclaveCount < enclave.enclaveQuantity; ++enclaveCount) {
      const enclaveName = `${enclave.enclaveClassName}-${++enclaveCountByName[
        enclave.enclaveClassName
      ]}`;
      const enclaveHosts: string[] = [];
      const enclavePortMapping: Record<string, PortMapping> = {};
      const wildcardPortMapHosts: string[] = [];

      // For each node instance group...
      for (const nodeInstances of enclaveClass.nodes) {
        const nodeClass = nodeClasses[nodeInstances.nodeClassName];

        // ...create instances of the node class of the desired quantity
        for (let nodeCount = 0; nodeCount < nodeInstances.nodeQuantity; ++nodeCount) {
          const nodeNumber = ++nodeCountByType[nodeClass.type];
          const nodeName = `race-${nodeClass.type}-${String(nodeNumber).padStart(5, '0')}`;

          // Add unique port mapping for the node, or add it to wildcard port mapping
          if (nodeInstances.portMapping.length > 0) {
            for (const portMapParams of nodeInstances.portMapping) {
              const externalPort = portMapParams.startExternalPort + nodeCount;
              enclavePortMapping[String(externalPort)] = {
                hosts: [nodeName],
                port: String(portMapParams.internalPort),
              };
            }
          } else {
            wildcardPortMapHosts.push(nodeName);
          }

          enclaveHosts.push(nodeName);
          rangeConfig.range.RACE_nodes.push({
            ...nodeClass,
            name: nodeName,
            enclave: enclaveName,
            identities: [],
          });
        }
      }

      if (wildcardPortMapHosts.length > 0) {
        enclavePortMapping['*'] = {
          hosts: wildcardPortMapHosts,
          port: '*',
        };
      }

      rangeConfig.range.enclaves.push({
        name: enclaveName,
        ip: enclaveName,
        hosts: enclaveHosts,
        port_mapping: enclavePortMapping,
      });
    }
  }

  return rangeConfig;
};
