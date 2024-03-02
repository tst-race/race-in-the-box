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

import { Button, Classes } from '@blueprintjs/core';
import clsx from 'clsx';

import { KitSourceType } from '../../types';

import styles from './KitSourceTypePanel.module.css';

export interface KitSourceTypePanelProps {
  allowCore: boolean;
  onSelect: (val: KitSourceType) => void;
}

export const KitSourceTypePanel = ({ allowCore, onSelect }: KitSourceTypePanelProps) => (
  <div className={clsx(Classes.DIALOG_BODY, styles.body)}>
    {allowCore && <Button onClick={() => onSelect('core')} text="Use kit from RACE core" />}
    <Button onClick={() => onSelect('local')} text="Use kit from local filesystem" />
    <Button onClick={() => onSelect('remote')} text="Download kit from remote URL" />
    <Button onClick={() => onSelect('tag')} text="Download kit from GitHub tagged release" />
    <Button
      onClick={() => onSelect('branch')}
      text="Download kit from latest GitHub Actions workflow run for branch"
    />
    <Button
      onClick={() => onSelect('run')}
      text="Download kit from specific GitHub Actions workflow run"
    />
  </div>
);
