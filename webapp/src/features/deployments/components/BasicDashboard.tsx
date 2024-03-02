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

import { useActiveDeployment } from '../api/getActiveDeployment';
import { useDeployments } from '../api/getDeployments';
import { DeploymentMode } from '../types';

import { DeploymentCard } from './DeploymentCard/DeploymentCard';

export type BasicDashboardTypes = {
  mode: DeploymentMode;
};

export const BasicDashboard = ({ mode }: BasicDashboardTypes) => {
  const activeQuery = useActiveDeployment({ mode });
  const allQuery = useDeployments({ mode });

  return (
    <>
      <H3>Active Deployment</H3>
      {activeQuery.isLoading && <DeploymentCard name="" skeleton />}
      {activeQuery.isSuccess && !activeQuery.data.name && (
        <NonIdealState title="No deployments are active" />
      )}
      {activeQuery.data?.name && <DeploymentCard name={activeQuery.data.name} />}
      <H3>All Deployments</H3>
      {allQuery.isLoading && <DeploymentCard name="" skeleton />}
      {allQuery.isSuccess && allQuery.data.compatible.length == 0 && (
        <NonIdealState title={`No ${mode} deployments exist`} />
      )}
      {allQuery.data &&
        allQuery.data.compatible.map(({ name }) => <DeploymentCard key={name} name={name} />)}
    </>
  );
};
