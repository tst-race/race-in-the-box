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

import { Alert } from '@blueprintjs/core';
import { useEffect, useState } from 'react';

import { useMultiRowSelect } from '@/hooks/useMultiRowSelect';

import { useDeploymentNodes } from '../hooks/useDeploymentNodes';
import { useNodeActions } from '../hooks/useNodeActions';
import { useNodeFilter } from '../hooks/useNodeFilter';
import { DeploymentMode } from '../types';

import { NodeActionsToolbar } from './NodeActionsToolbar';
import { NodeFilterInput } from './NodeFilterInput';
import { NodeStateVisualization } from './NodeStateVisualization';
import { NodeTable } from './NodeTable';

export type DeploymentNodeListProps = {
  mode: DeploymentMode;
  name: string;
  omitContainers?: boolean;
};

export const DeploymentNodeList = ({
  mode,
  name,
  omitContainers = false,
}: DeploymentNodeListProps) => {
  const { filters, nodeFilter, setFilters } = useNodeFilter();
  const { isLoading, nodes } = useDeploymentNodes({
    filter: nodeFilter,
    mode,
    name,
    omitContainers,
  });

  const { selection, setSelection, trProps } = useMultiRowSelect();
  useEffect(() => setSelection([]), [filters, setSelection]);

  const [force, setForce] = useState(false);
  useEffect(() => {
    if (selection.length == 0) {
      setForce(false);
    }
  }, [selection, setForce]);

  const [enableAll, setEnableAll] = useState(false);

  const { actions, allStatuses, canBootstrap, confirmAlertProps, onlyStatus } = useNodeActions({
    mode,
    name,
    nodes,
    selection,
  });

  return (
    <>
      <NodeActionsToolbar
        actions={actions}
        allStatuses={allStatuses}
        canBootstrap={canBootstrap}
        enableAllActions={enableAll}
        force={force}
        mode={mode}
        name={name}
        numSelected={selection.length}
        onChangeEnableAllActions={(enable) => setEnableAll(enable)}
        onChangeForce={(force) => setForce(force)}
        onlyStatus={onlyStatus}
      />
      <NodeStateVisualization
        allStatuses={allStatuses}
        canBootstrap={canBootstrap}
        enableAllActions={enableAll}
        filters={filters}
        force={force}
        numSelected={selection.length}
        setFilters={selection.length == 0 ? setFilters : undefined}
        onlyStatus={onlyStatus}
        {...actions}
      />
      <NodeFilterInput filters={filters} omitContainers={omitContainers} setFilters={setFilters} />
      <NodeTable
        isLoading={isLoading}
        nodes={nodes}
        omitContainers={omitContainers}
        selection={selection}
        setSelection={setSelection}
        trProps={trProps}
      />
      <Alert {...confirmAlertProps} />
    </>
  );
};
