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

import { EnclaveClassForm } from '@/features/range-config';

import { useEnclaveClassTemplate } from '../api/getEnclaveClassTemplate';
import { useEnclaveClassTemplates } from '../api/getEnclaveClassTemplates';
import { useNodeClassTemplates } from '../api/getNodeClassTemplates';
import { useUpdateEnclaveClassTemplate } from '../api/updateEnclaveClassTemplate';

type UpdateEnclaveClassTemplateProps = {
  name: string;
};

export const UpdateEnclaveClassTemplate = ({ name }: UpdateEnclaveClassTemplateProps) => {
  const { data } = useEnclaveClassTemplate({ name });
  const { data: nodesData } = useNodeClassTemplates();
  const { data: enclavesData } = useEnclaveClassTemplates();
  const { mutate } = useUpdateEnclaveClassTemplate();

  return (
    <EnclaveClassForm
      defaultValues={data && { nodeClasses: {}, ...data }}
      enclaveClasses={enclavesData ? enclavesData.enclaveClasses : []}
      isModify
      isTemplate
      nodeClasses={nodesData ? nodesData.nodeClasses : []}
      onSubmit={(data) => mutate({ data })}
    />
  );
};
