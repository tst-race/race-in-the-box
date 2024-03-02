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
import { useParams } from 'react-router-dom';

import { ActionButtons } from '@/components/ActionButtons';
import { Page } from '@/components/Page';

import { RemoveEnclaveClassTemplateButton } from '../components/RemoveEnclaveClassTemplateButton';
import { UpdateEnclaveClassTemplate } from '../components/UpdateEnclaveClassTemplate';

export const UpdateEnclaveClassTemplatePage = () => {
  const { name } = useParams();
  const breadcrumbs = useMemo(
    () => [
      { text: 'Templates', to: '../..' },
      { text: 'Enclave Classes', to: '..' },
      { text: name, to: '.' },
    ],
    [name]
  );

  return (
    <Page breadcrumbs={breadcrumbs} title={`Enclave Class Template | ${name}`}>
      {name && (
        <ActionButtons>
          <RemoveEnclaveClassTemplateButton name={name} />
        </ActionButtons>
      )}
      {name && <UpdateEnclaveClassTemplate name={name} />}
    </Page>
  );
};
