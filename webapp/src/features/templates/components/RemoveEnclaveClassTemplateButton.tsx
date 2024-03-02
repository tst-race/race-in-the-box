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

import { ConfirmationButton } from '@/components/ConfirmationButton';

import { useRemoveEnclaveClassTemplate } from '../api/removeEnclaveClassTemplate';

type RemoveEnclaveClassTemplateButtonProps = {
  name: string;
};

export const RemoveEnclaveClassTemplateButton = ({
  name,
}: RemoveEnclaveClassTemplateButtonProps) => {
  const navigate = useNavigate();
  const { mutate } = useRemoveEnclaveClassTemplate();

  const handleDelete = () => mutate({ name }, { onSuccess: () => navigate('..') });

  return (
    <ConfirmationButton
      alertProps={{
        cancelButtonText: 'Cancel',
        confirmButtonText: 'Delete',
      }}
      intent="danger"
      onClick={handleDelete}
      prompt={
        <>
          <p>{`Are you sure you want to delete enclave class template ${name}?`}</p>
          <p>This action cannot be undone.</p>
        </>
      }
      text="Delete Template"
    />
  );
};
