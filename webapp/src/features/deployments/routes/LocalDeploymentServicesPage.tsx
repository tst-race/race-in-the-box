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

import { ButtonGroup } from '@blueprintjs/core';
import React from 'react';
import { useParams } from 'react-router-dom';

import { ActionButtons } from '@/components/ActionButtons';
import { NavButton } from '@/components/NavButton';
import { Page } from '@/components/Page';
import { RefreshButton } from '@/components/RefreshButton';

import { deploymentKeys } from '../api/queryKeys';
import { DeploymentServiceList } from '../components/DeploymentServiceList';

export const LocalDeploymentServicesPage = () => {
  const { name } = useParams();
  const breadcrumbs = React.useMemo(
    () => [
      { text: 'Local Deployments', to: '../..' },
      { text: name, to: '..' },
      { text: 'Services', to: '.' },
    ],
    [name]
  );

  return (
    <Page breadcrumbs={breadcrumbs} title={`Local | ${name} Services`} width="full">
      <ActionButtons>
        <ButtonGroup>
          <RefreshButton queryKey={deploymentKeys.serviceStatus('local', name || '')} />
          <NavButton icon="changes" intent="primary" to="../nodes" text="Actions" />
        </ButtonGroup>
      </ActionButtons>
      {name && <DeploymentServiceList mode="local" name={name} />}
    </Page>
  );
};
