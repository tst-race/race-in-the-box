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

import { Dialog } from '@blueprintjs/core';
import React, { useState } from 'react';

import { KitSourcePanelProps, KitSourceType } from '../types';

import { ActionsRunKitSourcePanel } from './ActionsRunKitSourcePanel';
import { BranchKitSourcePanel } from './BranchKitSourcePanel';
import { CoreKitSourcePanel } from './CoreKitSourcePanel';
import { KitSourceTypePanel } from './KitSourceTypePanel';
import { LocalKitSourcePanel } from './LocalKitSourcePanel';
import { RemoteKitSourcePanel } from './RemoteKitSourcePanel';
import { TagKitSourcePanel } from './TagKitSourcePanel';

const panels: Record<KitSourceType, React.FC<KitSourcePanelProps>> = {
  core: CoreKitSourcePanel,
  local: LocalKitSourcePanel,
  remote: RemoteKitSourcePanel,
  tag: TagKitSourcePanel,
  branch: BranchKitSourcePanel,
  run: ActionsRunKitSourcePanel,
};

export interface KitSourceWizardDialogProps {
  allowCore: boolean;
  isOpen: boolean;
  onClose: () => void;
  onSelect: (value: string) => void;
}

export const KitSourceWizardDialog = ({
  allowCore,
  isOpen,
  onClose,
  onSelect,
}: KitSourceWizardDialogProps) => {
  const [sourceType, setSourceType] = useState<KitSourceType | null>(null);

  const handleReset = () => setSourceType(null);
  const handleClose = () => {
    setSourceType(null);
    onClose();
  };
  const handleSelect = (value: string) => {
    onSelect(value);
    handleClose();
  };

  const PanelType = sourceType ? panels[sourceType] : undefined;

  return (
    <Dialog
      isOpen={isOpen}
      onClose={handleClose}
      title={sourceType ? `Specify ${sourceType} source` : 'Select source type'}
    >
      {PanelType ? (
        <PanelType onReset={handleReset} onSelect={handleSelect} />
      ) : (
        <KitSourceTypePanel allowCore={allowCore} onSelect={setSourceType} />
      )}
    </Dialog>
  );
};
