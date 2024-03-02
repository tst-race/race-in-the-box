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

import { Route, Routes } from 'react-router-dom';

import { lazyImport } from '@/utils/lazyImport';

import { MessageAutoPageProp } from './MessageSendAutoPage';

const { MessageSendAutoPage } = lazyImport(
  () => import('./MessageSendAutoPage'),
  'MessageSendAutoPage'
);

const { MessageSendManualPage } = lazyImport(
  () => import('./MessageSendManualPage'),
  'MessageSendManualPage'
);

const { MessageListPage } = lazyImport(() => import('./MessageListPage'), 'MessageListPage');

export const MessagingRoutes = ({ mode }: MessageAutoPageProp) => (
  <Routes>
    <Route path="/send-auto" element={<MessageSendAutoPage mode={mode} />} />
    <Route path="/send-manual" element={<MessageSendManualPage mode={mode} />} />
    <Route path="/list" element={<MessageListPage mode={mode} />} />
  </Routes>
);
