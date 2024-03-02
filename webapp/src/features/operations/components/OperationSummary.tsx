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

import { Button, Card, H4, HTMLTable, Props } from '@blueprintjs/core';
import { MouseEvent } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButtons } from '@/components/ActionButtons';
import { toSearchQuery } from '@/utils/toSearchQuery';

import { useQueuedOperations } from '../api/getQueuedOperations';

export type OperationSummaryProps = Pick<Props, 'className'> & {
  targetName: string;
  targetType: string;
  title?: string;
};

export const OperationSummary = ({
  className,
  targetName,
  targetType,
  title = 'Recent Operations',
}: OperationSummaryProps) => {
  const navigate = useNavigate();
  const handleClick = () => navigate(`/operations?${toSearchQuery({ targetName, targetType })}`);

  const query = useQueuedOperations({ page: 1, size: 5, target: `${targetType}:${targetName}` });

  const handleRowClick = (id: number) => (event: MouseEvent<HTMLTableRowElement>) => {
    event.stopPropagation();
    navigate(`/operations/${id}`);
  };

  return (
    <Card className={className} interactive onClick={handleClick}>
      <H4>{title}</H4>
      <HTMLTable condensed interactive>
        <tbody>
          {query.data &&
            query.data.operations.map((operation) => (
              <tr key={operation.id} onClick={handleRowClick(operation.id)}>
                <td>{operation.stoppedTime}</td>
                <td>{operation.name}</td>
                <td>{operation.state}</td>
              </tr>
            ))}
        </tbody>
      </HTMLTable>
      <ActionButtons noMargin>
        <Button intent="primary" rightIcon="arrow-right" />
      </ActionButtons>
    </Card>
  );
};
