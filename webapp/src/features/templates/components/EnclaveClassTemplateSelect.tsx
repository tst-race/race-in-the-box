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

import { FormGroup, HTMLSelect } from '@blueprintjs/core';
import { ChangeEventHandler, useState } from 'react';

import { useEnclaveClassTemplate } from '../api/getEnclaveClassTemplate';
import { useEnclaveClassTemplates } from '../api/getEnclaveClassTemplates';
import { EnclaveClassTemplate } from '../types';

type EnclaveClassTemplateSelectProps = {
  onApply: (template: EnclaveClassTemplate) => void;
};

export const EnclaveClassTemplateSelect = ({ onApply }: EnclaveClassTemplateSelectProps) => {
  const [selected, setSelected] = useState<string | null>(null);
  const { data: allData } = useEnclaveClassTemplates();

  useEnclaveClassTemplate({
    name: selected || '',
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    config: { enabled: !!selected, onSuccess: onApply },
  });

  const handleChange: ChangeEventHandler<HTMLSelectElement> = (event) =>
    setSelected(event.currentTarget.value);

  return (
    <FormGroup inline label="Apply Enclave Class Template" labelFor="enclaveClassTemplate">
      <HTMLSelect
        disabled={!allData}
        id="enclaveClassTemplate"
        onChange={handleChange}
        options={['Select...', ...(allData?.enclaveClasses || [])]}
      />
    </FormGroup>
  );
};
