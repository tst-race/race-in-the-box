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

import clsx from 'clsx';
import React from 'react';

import styles from './ActionButtons.module.css';

type ActionButtonsProps = {
  children: React.ReactNode;
  noMargin?: boolean;
};

export const ActionButtons = ({ children, noMargin = false }: ActionButtonsProps) => (
  <div
    className={clsx(styles.buttons, {
      [styles.margins]: !noMargin,
      [styles.oneButton]: React.Children.count(children) == 1,
      [styles.multipleButtons]: React.Children.count(children) > 1,
    })}
  >
    {children}
  </div>
);
