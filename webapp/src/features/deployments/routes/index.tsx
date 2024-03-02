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

import { Navigate, Route, Routes } from 'react-router-dom';

import { ENABLE_AWS_DEPLOYMENTS } from '@/config';
import { MessagingRoutes } from '@/features/messaging';
import { lazyImport } from '@/utils/lazyImport';

const { CreateLocalDeploymentPage } = lazyImport(
  () => import('./CreateLocalDeploymentPage'),
  'CreateLocalDeploymentPage'
);
const { LocalDeploymentsDashboardPage } = lazyImport(
  () => import('./LocalDeploymentsDashboardPage'),
  'LocalDeploymentsDashboardPage'
);

const { LocalDeploymentOverviewPage } = lazyImport(
  () => import('./LocalDeploymentOverviewPage'),
  'LocalDeploymentOverviewPage'
);
const { LocalDeploymentConfigurationPage } = lazyImport(
  () => import('./LocalDeploymentConfigurationPage'),
  'LocalDeploymentConfigurationPage'
);
const { LocalDeploymentContainersPage } = lazyImport(
  () => import('./LocalDeploymentContainersPage'),
  'LocalDeploymentContainersPage'
);
const { LocalDeploymentNodesPage } = lazyImport(
  () => import('./LocalDeploymentNodesPage'),
  'LocalDeploymentNodesPage'
);
const { LocalDeploymentServicesPage } = lazyImport(
  () => import('./LocalDeploymentServicesPage'),
  'LocalDeploymentServicesPage'
);
const { LocalDeploymentGenerateConfigPage } = lazyImport(
  () => import('./LocalDeploymentGenerateConfigPage'),
  'LocalDeploymentGenerateConfigPage'
);
const { LocalDeploymentBootstrapNodePage } = lazyImport(
  () => import('./LocalDeploymentBootstrapNodePage'),
  'LocalDeploymentBootstrapNodePage'
);

const { AwsDeploymentsDashboardPage } = lazyImport(
  () => import('./AwsDeploymentsDashboardPage'),
  'AwsDeploymentsDashboardPage'
);

const { AwsDeploymentOverviewPage } = lazyImport(
  () => import('./AwsDeploymentOverviewPage'),
  'AwsDeploymentOverviewPage'
);
const { AwsDeploymentConfigurationPage } = lazyImport(
  () => import('./AwsDeploymentConfigurationPage'),
  'AwsDeploymentConfigurationPage'
);
const { AwsDeploymentNodesPage } = lazyImport(
  () => import('./AwsDeploymentNodesPage'),
  'AwsDeploymentNodesPage'
);
const { AwsDeploymentServicesPage } = lazyImport(
  () => import('./AwsDeploymentServicesPage'),
  'AwsDeploymentServicesPage'
);
const { AwsDeploymentGenerateConfigPage } = lazyImport(
  () => import('./AwsDeploymentGenerateConfigPage'),
  'AwsDeploymentGenerateConfigPage'
);
const { AwsDeploymentBootstrapNodePage } = lazyImport(
  () => import('./AwsDeploymentBootstrapNodePage'),
  'AwsDeploymentBootstrapNodePage'
);

const LocalDeploymentRoutes = () => (
  <Routes>
    <Route path="/config" element={<LocalDeploymentConfigurationPage />} />
    <Route path="/containers" element={<LocalDeploymentContainersPage />} />
    <Route path="/nodes" element={<LocalDeploymentNodesPage />} />
    <Route path="/services" element={<LocalDeploymentServicesPage />} />
    <Route path="/generate-config" element={<LocalDeploymentGenerateConfigPage />} />
    <Route path="/bootstrap-node" element={<LocalDeploymentBootstrapNodePage />} />
    <Route path="/messages/*" element={<MessagingRoutes mode="local" />} />
  </Routes>
);

const LocalDeploymentsRoutes = () => (
  <Routes>
    <Route path="/" element={<LocalDeploymentsDashboardPage />} />
    <Route path="/create" element={<CreateLocalDeploymentPage />} />
    <Route path="/:name" element={<LocalDeploymentOverviewPage />} />
    <Route path="/:name/*" element={<LocalDeploymentRoutes />} />
  </Routes>
);

const AwsDeploymentRoutes = () => (
  <Routes>
    <Route path="/config" element={<AwsDeploymentConfigurationPage />} />
    <Route path="/nodes" element={<AwsDeploymentNodesPage />} />
    <Route path="/services" element={<AwsDeploymentServicesPage />} />
    <Route path="/generate-config" element={<AwsDeploymentGenerateConfigPage />} />
    <Route path="/bootstrap-node" element={<AwsDeploymentBootstrapNodePage />} />
    <Route path="/messages/*" element={<MessagingRoutes mode="aws" />} />
  </Routes>
);

const AwsDeploymentsRoutes = () => (
  <Routes>
    <Route path="/" element={<AwsDeploymentsDashboardPage />} />
    <Route path="/:name" element={<AwsDeploymentOverviewPage />} />
    <Route path="/:name/*" element={<AwsDeploymentRoutes />} />
  </Routes>
);

export const DeploymentRoutes = () => (
  <Routes>
    {ENABLE_AWS_DEPLOYMENTS && <Route path="/aws/*" element={<AwsDeploymentsRoutes />} />}
    <Route path="/local/*" element={<LocalDeploymentsRoutes />} />
    <Route path="*" element={<Navigate to="/" />} />
  </Routes>
);
