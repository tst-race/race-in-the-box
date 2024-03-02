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

import { useDeploymentServiceStatus } from '../api/getDeploymentServiceStatus';
import { ServiceStatusValues, DeploymentMode } from '../types';
import { ServiceStatusColors } from '../utils/serviceStatusColors';

export type DeploymentServiceListProps = {
  mode: DeploymentMode;
  name: string;
};

export const DeploymentServiceList = ({ mode, name }: DeploymentServiceListProps) => {
  const { isLoading, data } = useDeploymentServiceStatus({ mode, name });

  return (
    <HTMLTable condensed striped>
      <thead>
        <tr>
          <th>Name</th>
          <th>Service Status</th>
          <th>Details</th>
        </tr>
      </thead>
      <tbody>
        {isLoading && (
          <tr>
            <td className={Classes.SKELETON}>Name</td>
            <td className={Classes.SKELETON}>Service Status</td>
            <td className={Classes.SKELETON}>Details</td>
          </tr>
        )}
        {data && (
          <>
            {data.children['External Services']?.children && (
              <>
                <tr>
                  <td>
                    <b>Comms External Services</b>
                  </td>
                  <td />
                  <td />
                </tr>
                {Object.entries(data.children['External Services'].children).map(
                  ([name, report]) => (
                    <tr key={name}>
                      <td>{name}</td>
                      <td>
                        <StateTag color={ServiceStatusColors[report.status]}>
                          {ServiceStatusValues[report.status]}
                        </StateTag>
                      </td>
                      <td>{report.reason}</td>
                    </tr>
                  )
                )}
              </>
            )}
            {data.children['RiB']?.children && (
              <>
                <tr>
                  <td>
                    <b>RiB Services</b>
                  </td>
                  <td />
                  <td />
                </tr>
                {Object.entries(data.children['RiB'].children).map(([name, report]) => (
                  <tr key={name}>
                    <td>{name}</td>
                    <td>
                      <StateTag color={ServiceStatusColors[report.status]}>
                        {ServiceStatusValues[report.status]}
                      </StateTag>
                    </td>
                    <td>{report.reason}</td>
                  </tr>
                ))}
              </>
            )}
          </>
        )}
      </tbody>
    </HTMLTable>
  );
};
