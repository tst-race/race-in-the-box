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

import { Button, Classes, Intent } from '@blueprintjs/core';
import clsx from 'clsx';
import { FormEventHandler } from 'react';

import styles from './KitSourcePanel.module.css';

export interface KitSourcePanelProps {
  children: React.ReactNode;
  onReset: () => void;
  onSubmit: FormEventHandler;
}

export const KitSourcePanel = ({ children, onReset, onSubmit }: KitSourcePanelProps) => (
  <>
    <div className={Classes.DIALOG_BODY}>{children}</div>
    <div className={Classes.DIALOG_FOOTER}>
      <div className={clsx(Classes.DIALOG_FOOTER_ACTIONS, styles.footer)}>
        <Button onClick={onReset} text="Back" />
        <Button onClick={onSubmit} intent={Intent.PRIMARY} text="OK" />
      </div>
    </div>
  </>
);
