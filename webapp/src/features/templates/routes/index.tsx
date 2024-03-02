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

import { lazyImport } from '@/utils/lazyImport';

const { TemplatesPage } = lazyImport(() => import('./TemplatesPage'), 'TemplatesPage');

const { NodeClassTemplatesPage } = lazyImport(
  () => import('./NodeClassTemplatesPage'),
  'NodeClassTemplatesPage'
);
const { CreateNodeClassTemplatePage } = lazyImport(
  () => import('./CreateNodeClassTemplatePage'),
  'CreateNodeClassTemplatePage'
);
const { UpdateNodeClassTemplatePage } = lazyImport(
  () => import('./UpdateNodeClassTemplatePage'),
  'UpdateNodeClassTemplatePage'
);

const { EnclaveClassTemplatesPage } = lazyImport(
  () => import('./EnclaveClassTemplatesPage'),
  'EnclaveClassTemplatesPage'
);
const { CreateEnclaveClassTemplatePage } = lazyImport(
  () => import('./CreateEnclaveClassTemplatePage'),
  'CreateEnclaveClassTemplatePage'
);
const { UpdateEnclaveClassTemplatePage } = lazyImport(
  () => import('./UpdateEnclaveClassTemplatePage'),
  'UpdateEnclaveClassTemplatePage'
);

const NodeClassTemplateRoutes = () => (
  <Routes>
    <Route path="/" element={<NodeClassTemplatesPage />} />
    <Route path="/create" element={<CreateNodeClassTemplatePage />} />
    <Route path="/:name" element={<UpdateNodeClassTemplatePage />} />
  </Routes>
);

const EnclaveClassTemplateRoutes = () => (
  <Routes>
    <Route path="/" element={<EnclaveClassTemplatesPage />} />
    <Route path="/create" element={<CreateEnclaveClassTemplatePage />} />
    <Route path="/:name" element={<UpdateEnclaveClassTemplatePage />} />
  </Routes>
);

export const TemplateRoutes = () => (
  <Routes>
    <Route path="/" element={<TemplatesPage />} />
    <Route path="/node-classes/*" element={<NodeClassTemplateRoutes />} />
    <Route path="/enclave-classes/*" element={<EnclaveClassTemplateRoutes />} />
    <Route path="*" element={<Navigate to="/" />} />
  </Routes>
);
