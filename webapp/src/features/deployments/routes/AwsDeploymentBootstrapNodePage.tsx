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
import { useParams, useSearchParams } from 'react-router-dom';

import { Page } from '@/components/Page';

import { BootstrapNodeForm } from '../components/BootstrapNodeForm';

export const AwsDeploymentBootstrapNodePage = () => {
  const { name } = useParams();
  const breadcrumbs = useMemo(
    () => [
      { text: 'AWS Deployments', to: '../..' },
      { text: name, to: '..' },
      { text: 'Bootstrap Node', to: '.' },
    ],
    [name]
  );

  const [searchParams] = useSearchParams({ force: 'false', target: '' });
  const force = searchParams.get('force') == 'true';
  const target = searchParams.get('target') || '';

  return (
    <Page breadcrumbs={breadcrumbs} title={`AWS | ${name} Bootstrap Node`}>
      {name && <BootstrapNodeForm force={force} mode="aws" name={name} target={target} />}
    </Page>
  );
};
