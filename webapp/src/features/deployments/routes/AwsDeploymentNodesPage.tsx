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

import React from 'react';
import { useParams } from 'react-router-dom';

import { Page } from '@/components/Page';

import { DeploymentNodeList } from '../components/DeploymentNodeList';

export const AwsDeploymentNodesPage = () => {
  const { name } = useParams();
  const breadcrumbs = React.useMemo(
    () => [
      { text: 'AWS Deployments', to: '../..' },
      { text: name, to: '..' },
      { text: 'Nodes', to: '.' },
    ],
    [name]
  );

  return (
    <Page breadcrumbs={breadcrumbs} title={`AWS | ${name} Nodes`} width="full">
      {name && <DeploymentNodeList mode="aws" name={name} omitContainers />}
    </Page>
  );
};
