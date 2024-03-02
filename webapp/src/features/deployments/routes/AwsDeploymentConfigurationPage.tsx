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

import { Tab, Tabs } from '@blueprintjs/core';
import React from 'react';
import { useParams } from 'react-router-dom';

import { Page } from '@/components/Page';

import { AwsDeploymentConfigFacts } from '../components/AwsDeploymentConfigFacts';
import { AwsDeploymentMetadataFacts } from '../components/AwsDeploymentMetadataFacts';
import { AwsDeploymentNodeFacts } from '../components/AwsDeploymentNodeFacts';

export const AwsDeploymentConfigurationPage = () => {
  const { name } = useParams();
  const breadcrumbs = React.useMemo(
    () => [
      { text: 'AWS Deployments', to: '../..' },
      { text: name, to: '..' },
      { text: 'Configuration', to: '.' },
    ],
    [name]
  );

  return (
    <Page breadcrumbs={breadcrumbs} title={`AWS | ${name} Configuration`}>
      {name && (
        <Tabs id="aws-deployment-configuration">
          <Tab id="config" title="Config" panel={<AwsDeploymentConfigFacts name={name} />} />
          <Tab id="nodes" title="Nodes" panel={<AwsDeploymentNodeFacts name={name} />} />
          <Tab id="metadata" title="Metadata" panel={<AwsDeploymentMetadataFacts name={name} />} />
        </Tabs>
      )}
    </Page>
  );
};
