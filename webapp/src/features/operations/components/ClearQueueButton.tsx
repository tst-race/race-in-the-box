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

import { ConfirmationButton } from '@/components/ConfirmationButton';

import { useClearOperationsQueue } from '../api/clearOperationsQueue';

export const ClearQueueButton = () => {
  const { mutate } = useClearOperationsQueue();

  return (
    <ConfirmationButton
      alertProps={{
        cancelButtonText: 'Cancel',
        confirmButtonText: 'Clear Queue',
      }}
      intent="danger"
      onClick={() => mutate()}
      prompt={
        <>
          <p>
            Clearing the queue will remove all records of prior operations and logs. Are you sure
            you want to continue?
          </p>
          <p>This action cannot be undone.</p>
        </>
      }
      text="Delete all"
    />
  );
};
