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

import { ButtonGroup, Divider } from '@blueprintjs/core';

import {
  RangeConfigGenerationParametersMethods,
  RangeConfigGenerationParametersState,
} from '../../hooks/useRangeConfigGenerationParameters';

import { AddNewButton } from './AddNewButton';
import { DeleteButton } from './DeleteButton';
import { DuplicateButton } from './DuplicateButton';

type RangeConfigGenParamsToolbarProps = {
  methods: RangeConfigGenerationParametersMethods;
  selectedTreeNode: RangeConfigGenerationParametersState['selectedTreeNode'];
};

export const RangeConfigGenParamsToolbar = ({
  methods,
  selectedTreeNode,
}: RangeConfigGenParamsToolbarProps) => (
  <ButtonGroup>
    <AddNewButton
      onShowAddEnclave={() => methods.showAddNewForm('enclave')}
      onShowAddEnclaveClass={() => methods.showAddNewForm('enclaveClass')}
      onShowAddNodeClass={() => methods.showAddNewForm('nodeClass')}
      selectedTreeNode={selectedTreeNode}
    />
    <Divider />
    <DuplicateButton
      onDuplicateEnclave={methods.duplicateEnclave}
      onDuplicateEnclaveClass={methods.duplicateEnclaveClass}
      onDuplicateNodeClass={methods.duplicateNodeClass}
      selectedTreeNode={selectedTreeNode}
    />
    <DeleteButton
      onDeleteEnclave={methods.removeEnclave}
      onDeleteEnclaveClass={methods.removeEnclaveClass}
      onDeleteNodeClass={methods.removeNodeClass}
      selectedTreeNode={selectedTreeNode}
    />
  </ButtonGroup>
);
