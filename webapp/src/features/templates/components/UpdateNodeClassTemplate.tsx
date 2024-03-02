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

import { NodeClassForm } from '@/features/range-config';

import { useNodeClassTemplate } from '../api/getNodeClassTemplate';
import { useNodeClassTemplates } from '../api/getNodeClassTemplates';
import { useUpdateNodeClassTemplate } from '../api/updateNodeClassTemplate';

type UpdateNodeClassTemplateProps = {
  name: string;
};

export const UpdateNodeClassTemplate = ({ name }: UpdateNodeClassTemplateProps) => {
  const { data } = useNodeClassTemplate({ name });
  const { data: allData } = useNodeClassTemplates();
  const { mutate } = useUpdateNodeClassTemplate();

  return (
    <NodeClassForm
      defaultValues={data}
      isModify
      isTemplate
      nodeClasses={allData ? allData.nodeClasses : []}
      onSubmit={(data) => mutate({ data })}
    />
  );
};
