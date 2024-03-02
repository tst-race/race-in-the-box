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

import { Page } from '@/components/Page';

import { AdvancedDashboard } from '../components/AdvancedDashboard';
import { BasicDashboard } from '../components/BasicDashboard';

const BREADCRUMBS = [{ text: 'Local Deployments', to: '.' }];

export const LocalDeploymentsDashboardPage = () => (
  <Page breadcrumbs={BREADCRUMBS} title="Local Deployments">
    <Tabs id="local-deployments-dashboard">
      <Tab id="basic" title="Basic" panel={<BasicDashboard mode="local" />} />
      <Tab id="advanced" title="Advanced" panel={<AdvancedDashboard mode="local" />} />
    </Tabs>
  </Page>
);
