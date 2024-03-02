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

import { Suspense } from 'react';
import { Navigate, Outlet, useRoutes } from 'react-router-dom';

import { MainLayout } from '@/components/MainLayout';
import { lazyImport } from '@/utils/lazyImport';

const { ConfigRoutes } = lazyImport(() => import('@/features/config'), 'ConfigRoutes');
const { DeploymentRoutes } = lazyImport(() => import('@/features/deployments'), 'DeploymentRoutes');
const { OperationRoutes } = lazyImport(() => import('@/features/operations'), 'OperationRoutes');
const { TemplateRoutes } = lazyImport(() => import('@/features/templates'), 'TemplateRoutes');

const App = () => (
  <MainLayout>
    <Suspense fallback={<div>loading...</div>}>
      <Outlet />
    </Suspense>
  </MainLayout>
);

export const AppRoutes = () => {
  const element = useRoutes([
    {
      path: '/',
      element: <App />,
      children: [
        { path: '/config/*', element: <ConfigRoutes /> },
        { path: '/deployments/*', element: <DeploymentRoutes /> },
        { path: '/operations/*', element: <OperationRoutes /> },
        { path: '/templates/*', element: <TemplateRoutes /> },
        { path: '*', element: <Navigate to="." /> },
      ],
    },
  ]);
  return element;
};
