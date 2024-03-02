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

import { Classes, HTMLTable, H4 } from '@blueprintjs/core';

import { useAwsDeploymentConfigSummary } from '../hooks/useAwsDeploymentConfigSummary';

export type AwsDeploymentNodeFactsProps = {
  name: string;
};

export const AwsDeploymentNodeFacts = ({ name }: AwsDeploymentNodeFactsProps) => {
  const { info, isLoading } = useAwsDeploymentConfigSummary({ name });

  return (
    <>
      <H4>Deployment Nodes</H4>
      <HTMLTable condensed striped>
        <thead>
          <tr>
            <th>Persona</th>
            <th>Node Type</th>
            <th>Platform</th>
            <th>Arch</th>
            <th>Genesis?</th>
            <th>Bridged?</th>
            <th>Has GPU?</th>
          </tr>
        </thead>
        <tbody>
          {isLoading && (
            <tr>
              <td className={Classes.SKELETON} />
              <td className={Classes.SKELETON} />
              <td className={Classes.SKELETON} />
              <td className={Classes.SKELETON} />
              <td className={Classes.SKELETON} />
              <td className={Classes.SKELETON} />
              <td className={Classes.SKELETON} />
            </tr>
          )}
          {info &&
            Object.keys(info.config.nodes)
              .sort()
              .map((persona) => ({ persona, ...info.config.nodes[persona] }))
              .map((config) => (
                <tr key={config.persona}>
                  <td>{config.persona}</td>
                  <td>{config.node_type}</td>
                  <td>{config.platform}</td>
                  <td>{config.architecture}</td>
                  <td>{config.genesis ? 'yes' : 'no'}</td>
                  <td>{config.bridge ? 'yes' : 'no'}</td>
                  <td>{config.gpu ? 'yes' : 'no'}</td>
                </tr>
              ))}
        </tbody>
      </HTMLTable>
    </>
  );
};
