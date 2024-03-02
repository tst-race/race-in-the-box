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

import { Button, Menu, MenuDivider, MenuItem } from '@blueprintjs/core';
import { Popover2 } from '@blueprintjs/popover2';

import { NodeActions, NodeStatus } from '../types';

const configStatuses: (NodeStatus | null)[] = ['READY_TO_GENERATE_CONFIG', 'READY_TO_TAR_CONFIGS'];
const upStatuses: (NodeStatus | null)[] = [
  'DOWN',
  'READY_TO_PUBLISH_CONFIGS',
  'READY_TO_INSTALL_CONFIGS',
];

type NodeActionsButtonProps = NodeActions & {
  canBootstrap: boolean;
  disabled: boolean;
  force: boolean;
  numSelected: number;
  status: NodeStatus | null;
};

export const NodeActionsButton = ({
  canBootstrap,
  disabled,
  force,
  numSelected,
  onBootstrap,
  onClear,
  onGenerateConfigs,
  onInstallConfigs,
  onPublishConfigs,
  onReset,
  onStart,
  onStop,
  onTarConfigs,
  onTearDown,
  onStandUp,
  status,
}: NodeActionsButtonProps) => {
  const menu = (
    <Menu>
      <MenuItem disabled={!force && !configStatuses.includes(status)} text="Generate Configs">
        <MenuItem
          disabled={status != 'READY_TO_GENERATE_CONFIG' && !force}
          onClick={() => onGenerateConfigs(force, false)}
          text="Generate and Create Archive"
        />
        <MenuDivider />
        <MenuItem
          disabled={status != 'READY_TO_GENERATE_CONFIG' && !force}
          onClick={() => onGenerateConfigs(force, true)}
          text="Generate Only"
        />
        <MenuItem
          disabled={status != 'READY_TO_TAR_CONFIGS' && !force}
          onClick={() => onTarConfigs(force)}
          text="Create Config Archive"
        />
      </MenuItem>
      <MenuItem disabled={!force && !upStatuses.includes(status)} text="Stand Up">
        <MenuItem
          disabled={status != 'DOWN' && !force}
          onClick={() => onStandUp(force, false)}
          text="Fully Stand Up"
        />
        <MenuDivider />
        <MenuItem
          disabled={status != 'DOWN' && !force}
          onClick={() => onStandUp(force, true)}
          text="Stand Up Without Configs"
        />
        <MenuItem
          disabled={status != 'READY_TO_PUBLISH_CONFIGS' && !force}
          onClick={() => onPublishConfigs(force)}
          text="Publish Configs To File Server"
        />
        <MenuItem
          disabled={status != 'READY_TO_INSTALL_CONFIGS' && !force}
          onClick={() => onInstallConfigs(force)}
          text="Install Configs On Node"
        />
      </MenuItem>
      {canBootstrap && (
        <MenuItem
          disabled={numSelected != 1 || (status != 'READY_TO_BOOTSTRAP' && !force)}
          onClick={() => onBootstrap(force)}
          text="Bootstrap Into Network"
        />
      )}
      <MenuItem
        disabled={status != 'READY_TO_START' && status != 'STOPPED' && !force}
        onClick={() => onStart(force)}
        text="Start"
      />
      <MenuDivider />
      <MenuItem
        disabled={status != 'INITIALIZING' && status != 'RUNNING' && !force}
        onClick={() => onStop(force)}
        text="Stop"
      />
      <MenuItem
        disabled={status != 'STOPPED' && !force}
        onClick={() => onReset(force)}
        text="Reset To Genesis State"
      />
      <MenuItem
        disabled={status != 'STOPPED' && !force}
        onClick={() => onClear(force)}
        text="Clear Configs"
      />
      <MenuItem
        disabled={status != 'STOPPED' && !force}
        onClick={() => onTearDown(force)}
        text="Tear Down"
      />
    </Menu>
  );

  return (
    <Popover2 content={menu} minimal placement="bottom-start">
      <Button
        disabled={disabled}
        icon="changes"
        intent="primary"
        rightIcon="chevron-down"
        text="Actions"
      />
    </Popover2>
  );
};
