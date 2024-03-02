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

import { Button, ButtonGroup } from '@blueprintjs/core';
import { useNavigate } from 'react-router-dom';

import { useCancelOperation } from '../../api/cancelOperation';
import { useRetryOperation } from '../../api/retryOperation';
import { OperationState } from '../../types';

type OperationActionsProps = {
  id: number;
  name: string;
  state: OperationState;
};

export const OperationActions = ({ id, name, state }: OperationActionsProps) => {
  const navigate = useNavigate();

  const { mutate: cancel } = useCancelOperation();
  const handleCancel = () => cancel({ id, name });

  const { mutate: retry } = useRetryOperation();
  const handleRetry = () =>
    retry(
      { id, name },
      {
        onSuccess: (result) => navigate(`/operations/${result.id}`),
      }
    );

  return (
    <ButtonGroup>
      {state == 'PENDING' && <Button icon="disable" onClick={handleCancel} />}
      {(state == 'CANCELLED' || state == 'SUCCEEDED' || 'FAILED' || state == 'ABORTED') && (
        <Button icon="refresh" onClick={handleRetry} />
      )}
    </ButtonGroup>
  );
};
