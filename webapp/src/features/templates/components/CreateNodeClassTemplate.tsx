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

import { useNavigate } from 'react-router-dom';

import { NodeClassForm } from '@/features/range-config';

import { useCreateNodeClassTemplate } from '../api/createNodeClassTemplate';
import { useNodeClassTemplates } from '../api/getNodeClassTemplates';
import { NodeClassTemplate } from '../types';

export const CreateNodeClassTemplate = () => {
  const navigate = useNavigate();
  const { data } = useNodeClassTemplates();
  const { mutate } = useCreateNodeClassTemplate();

  const handleSubmit = (data: NodeClassTemplate) =>
    mutate(
      { data },
      {
        onSuccess: () => navigate('..'),
      }
    );

  return (
    <NodeClassForm isTemplate nodeClasses={data ? data.nodeClasses : []} onSubmit={handleSubmit} />
  );
};
