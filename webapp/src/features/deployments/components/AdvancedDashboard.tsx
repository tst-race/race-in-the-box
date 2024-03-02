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

import { H3, NonIdealState } from '@blueprintjs/core';

import { useDeployments } from '../api/getDeployments';
import { DeploymentMode } from '../types';

import { DeploymentCard } from './DeploymentCard/DeploymentCard';

export type AdvancedDashboardTypes = {
  mode: DeploymentMode;
};

export const AdvancedDashboard = ({ mode }: AdvancedDashboardTypes) => {
  const allQuery = useDeployments({ mode });

  return (
    <>
      <H3>Incompatible Deployments</H3>
      {allQuery.isLoading && <DeploymentCard name="" skeleton />}
      {allQuery.isSuccess && allQuery.data.incompatible.length == 0 && (
        <NonIdealState title={`No incompatible ${mode} deployments exist`} />
      )}
      {allQuery.data &&
        allQuery.data.incompatible.map(({ name, rib_version }) => (
          <DeploymentCard key={name} name={name} ribVersion={rib_version} />
        ))}
    </>
  );
};
