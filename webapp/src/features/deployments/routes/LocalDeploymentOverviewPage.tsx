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

import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { Grid, spanCol1and2ClassName } from '@/components/Grid';
import { Page } from '@/components/Page';
import { OperationSummary } from '@/features/operations';

import { DeploymentActionsSummary } from '../components/DeploymentActionsSummary';
import { LocalDeploymentConfigSummary } from '../components/DeploymentConfigSummary';
import { DeploymentContainerSummary } from '../components/DeploymentContainerSummary';
import { DeploymentNodeSummary } from '../components/DeploymentNodeSummary';
import { DeploymentServiceSummary } from '../components/DeploymentServiceSummary';

export const LocalDeploymentOverviewPage = () => {
  const { name } = useParams();
  const breadcrumbs = useMemo(
    () => [
      { text: 'Local Deployments', to: '..' },
      { text: name, to: '.' },
    ],
    [name]
  );

  return (
    <Page breadcrumbs={breadcrumbs} title={`Local | ${name}`}>
      {name && (
        <Grid numCol={2}>
          <LocalDeploymentConfigSummary name={name} />
          <DeploymentActionsSummary mode="local" name={name} />
          <OperationSummary
            className={spanCol1and2ClassName}
            targetType="deployment:local"
            targetName={name}
          />
          <DeploymentNodeSummary mode="local" name={name} />
          <DeploymentContainerSummary mode="local" name={name} />
          <DeploymentServiceSummary mode="local" name={name} />
        </Grid>
      )}
    </Page>
  );
};
