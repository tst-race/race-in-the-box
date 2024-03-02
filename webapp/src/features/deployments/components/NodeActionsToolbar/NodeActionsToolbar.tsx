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

import { ButtonGroup, Checkbox } from '@blueprintjs/core';

import { RefreshButton } from '@/components/RefreshButton';

import { deploymentKeys } from '../../api/queryKeys';
import { DeploymentMode, NodeActions, NodeStatus } from '../../types';
import { NodeActionsButton } from '../NodeActionsButton';

import styles from './NodeActionsToolbar.module.css';

type NodeActionsToolbarProps = {
  actions: NodeActions;
  allStatuses: NodeStatus[];
  canBootstrap: boolean;
  enableAllActions: boolean;
  force: boolean;
  mode: DeploymentMode;
  name: string;
  numSelected: number;
  onChangeEnableAllActions: (enable: boolean) => void;
  onChangeForce: (force: boolean) => void;
  onlyStatus: NodeStatus | null;
};

export const NodeActionsToolbar = ({
  actions,
  allStatuses,
  canBootstrap,
  enableAllActions,
  force,
  mode,
  name,
  numSelected,
  onlyStatus,
  onChangeEnableAllActions,
  onChangeForce,
}: NodeActionsToolbarProps) => (
  <div className={styles.toolbar}>
    <div className={styles.toolbarLeft}>
      {numSelected > 0 && (
        <>
          <span>{numSelected} Nodes selected</span>
          {allStatuses.length > 1 && (
            <span className={styles.statusWarning}>Selected nodes have mixed status</span>
          )}
        </>
      )}
      {numSelected == 0 && allStatuses.length > 1 && (
        <span className={styles.statusWarning}>Deployment nodes have mixed status</span>
      )}
      <Checkbox
        className={styles.checkbox}
        checked={force}
        label="Force Operation"
        onChange={(event) => onChangeForce(event.currentTarget.checked)}
      />
      <Checkbox
        className={styles.checkbox}
        checked={enableAllActions}
        label="Enable Advanced Actions"
        onChange={(event) => onChangeEnableAllActions(event.currentTarget.checked)}
      />
    </div>
    <div className={styles.toolbarRight}>
      <ButtonGroup>
        <RefreshButton queryKey={deploymentKeys.nodeStatus(mode, name)} />
        <NodeActionsButton
          canBootstrap={canBootstrap}
          disabled={allStatuses.length > 1 && !force}
          force={force}
          numSelected={numSelected}
          status={onlyStatus}
          {...actions}
        />
      </ButtonGroup>
    </div>
  </div>
);
