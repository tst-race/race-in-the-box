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

import { Button, Card, H4 } from '@blueprintjs/core';
import { useNavigate } from 'react-router-dom';

import { ActionButtons } from '@/components/ActionButtons';
import { StatusCountSummary } from '@/components/StatusCountSummary';

import { useDeploymentNodeStatusSummary } from '../hooks/useDeploymentNodeStatusSummary';
import { DeploymentMode, NodeStatusValues } from '../types';

export type DeploymentNodeSummaryProps = {
  mode: DeploymentMode;
  name: string;
};

export const DeploymentNodeSummary = ({ mode, name }: DeploymentNodeSummaryProps) => {
  const navigate = useNavigate();
  const handleClick = () => navigate('nodes');

  const { byStatus, isLoading, total } = useDeploymentNodeStatusSummary({ mode, name });

  return (
    <Card interactive onClick={handleClick}>
      <H4>Nodes</H4>
      <StatusCountSummary
        counts={byStatus}
        isLoading={isLoading}
        labels={NodeStatusValues}
        total={total}
      />
      <ActionButtons noMargin>
        <Button intent="primary" rightIcon="arrow-right" />
      </ActionButtons>
    </Card>
  );
};
