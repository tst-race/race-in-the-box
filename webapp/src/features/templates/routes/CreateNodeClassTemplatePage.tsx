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

import { Page } from '@/components/Page';

import { CreateNodeClassTemplate } from '../components/CreateNodeClassTemplate';

const BREADCRUMBS = [
  { text: 'Templates', to: '../..' },
  { text: 'Node Classes', to: '..' },
  { text: 'Create New Template', to: '.' },
];

export const CreateNodeClassTemplatePage = () => (
  <Page breadcrumbs={BREADCRUMBS} title="Create Node Class Template">
    <CreateNodeClassTemplate />
  </Page>
);