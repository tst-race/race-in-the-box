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

import { Button } from '@blueprintjs/core';
import { useMemo } from 'react';

import { RangeConfigGenerationParametersState } from '../../hooks/useRangeConfigGenerationParameters';

type DuplicateButtonProps = {
  onDuplicateEnclave: (index: number) => void;
  onDuplicateEnclaveClass: (name: string) => void;
  onDuplicateNodeClass: (name: string) => void;
  selectedTreeNode: RangeConfigGenerationParametersState['selectedTreeNode'];
};

export const DuplicateButton = ({
  onDuplicateEnclave,
  onDuplicateEnclaveClass,
  onDuplicateNodeClass,
  selectedTreeNode,
}: DuplicateButtonProps) => {
  const handleClick = useMemo(() => {
    switch (selectedTreeNode?.type) {
      case 'nodeClass':
        return () => onDuplicateNodeClass(selectedTreeNode.name);
      case 'enclaveClass':
        return () => onDuplicateEnclaveClass(selectedTreeNode.name);
      case 'enclave':
        return () => onDuplicateEnclave(selectedTreeNode.index);
      default:
        return undefined;
    }
  }, [onDuplicateEnclave, onDuplicateEnclaveClass, onDuplicateNodeClass, selectedTreeNode]);

  return (
    <Button
      disabled={handleClick == undefined}
      icon="duplicate"
      onClick={handleClick}
      text="Duplicate"
    />
  );
};
