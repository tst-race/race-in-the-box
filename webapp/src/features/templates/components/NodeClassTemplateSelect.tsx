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

import { useNodeClassTemplate } from '../api/getNodeClassTemplate';
import { useNodeClassTemplates } from '../api/getNodeClassTemplates';
import { NodeClassTemplate } from '../types';

type NodeClassTemplateSelectProps = {
  onApply: (template: NodeClassTemplate) => void;
};

export const NodeClassTemplateSelect = ({ onApply }: NodeClassTemplateSelectProps) => {
  const [selected, setSelected] = useState<string | null>(null);
  const { data: allData } = useNodeClassTemplates();

  useNodeClassTemplate({
    name: selected || '',
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    config: { enabled: !!selected, onSuccess: onApply },
  });

  const handleChange: ChangeEventHandler<HTMLSelectElement> = (event) =>
    setSelected(event.currentTarget.value);

  return (
    <FormGroup inline label="Apply Node Class Template" labelFor="nodeClassTemplate">
      <HTMLSelect
        disabled={!allData}
        id="nodeClassTemplate"
        onChange={handleChange}
        options={['Select...', ...(allData?.nodeClasses || [])]}
      />
    </FormGroup>
  );
};
