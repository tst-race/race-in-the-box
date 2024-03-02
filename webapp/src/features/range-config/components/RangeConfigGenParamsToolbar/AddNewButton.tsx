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

import { Button, ButtonGroup, Menu, MenuItem } from '@blueprintjs/core';
import { Popover2 } from '@blueprintjs/popover2';
import { useMemo } from 'react';

import { RangeConfigGenerationParametersState } from '../../hooks/useRangeConfigGenerationParameters';

type AddNewButtonProps = {
  onShowAddEnclave: () => void;
  onShowAddEnclaveClass: () => void;
  onShowAddNodeClass: () => void;
  selectedTreeNode: RangeConfigGenerationParametersState['selectedTreeNode'];
};

export const AddNewButton = ({
  onShowAddEnclave,
  onShowAddEnclaveClass,
  onShowAddNodeClass,
  selectedTreeNode,
}: AddNewButtonProps) => {
  const [handleAdd, addText] = useMemo(() => {
    if (selectedTreeNode?.type.startsWith('enclaveClass')) {
      return [onShowAddEnclaveClass, 'Add Enclave Class'];
    }
    if (selectedTreeNode?.type.startsWith('enclave')) {
      return [onShowAddEnclave, 'Add Enclave'];
    }
    return [onShowAddNodeClass, 'Add Node Class'];
  }, [onShowAddEnclave, onShowAddEnclaveClass, onShowAddNodeClass, selectedTreeNode]);

  const buttonMenu = (
    <Menu>
      <MenuItem onClick={onShowAddNodeClass} text="Add Node Class" />
      <MenuItem onClick={onShowAddEnclaveClass} text="Add Enclave Class" />
      <MenuItem onClick={onShowAddEnclave} text="Add Enclave" />
    </Menu>
  );

  return (
    <ButtonGroup>
      <Button icon="add" onClick={handleAdd} text={addText} />
      <Popover2 content={buttonMenu} placement="bottom-start">
        <Button icon="chevron-down" />
      </Popover2>
    </ButtonGroup>
  );
};
