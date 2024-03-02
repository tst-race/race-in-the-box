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

import { Classes, HTMLTable } from '@blueprintjs/core';

import { StateTag } from '@/features/state-visualization';

import { useDeploymentContainerStatus } from '../api/getDeploymentContainerStatus';
import { ContainerStatusValues, DeploymentMode } from '../types';
import { ContainerStatusColors } from '../utils/containerStatusColors';

export type DeploymentContainerListProps = {
  mode: DeploymentMode;
  name: string;
};

export const DeploymentContainerList = ({ mode, name }: DeploymentContainerListProps) => {
  const { isLoading, data } = useDeploymentContainerStatus({ mode, name });

  return (
    <HTMLTable condensed striped>
      <thead>
        <tr>
          <th>Name</th>
          <th>Container Status</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        {isLoading && (
          <tr>
            <td className={Classes.SKELETON}>Name</td>
            <td className={Classes.SKELETON}>Container Status</td>
            <td className={Classes.SKELETON}>Details</td>
          </tr>
        )}
        {data &&
          Object.entries(data.children).map(([name, report]) => (
            <tr key={name}>
              <td>{name}</td>
              <td>
                <StateTag color={ContainerStatusColors[report.status]}>
                  {ContainerStatusValues[report.status]}
                </StateTag>
              </td>
              <td>{report.reason}</td>
            </tr>
          ))}
      </tbody>
    </HTMLTable>
  );
};
