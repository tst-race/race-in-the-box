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

import { ActionButtons } from '@/components/ActionButtons';
import { NavButton } from '@/components/NavButton';
import { Page } from '@/components/Page';

import { EnclaveClassTemplates } from '../components/EnclaveClassTemplates';

const BREADCRUMBS = [
  // A destination of '..' ends up back on this page, because this is the root page
  // within its parent Routes. In order to get up to the Templates page in the ancestor
  // Routes, we have to use '../..'.
  { text: 'Templates', to: '../..' },
  { text: 'Enclave Classes', to: '.' },
];

export const EnclaveClassTemplatesPage = () => (
  <Page breadcrumbs={BREADCRUMBS} title="Enclave Class Templates">
    <ActionButtons>
      <NavButton intent="primary" text="Create New Template" to="create" />
    </ActionButtons>
    <EnclaveClassTemplates />
  </Page>
);
