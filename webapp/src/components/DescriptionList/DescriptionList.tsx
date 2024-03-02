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

import { Classes } from '@blueprintjs/core';
import clsx from 'clsx';
import { ReactNode } from 'react';

import styles from './DescriptionList.module.css';

export type DescriptionListProps = {
  children: ReactNode;
  margin?: boolean;
  pending?: boolean;
  striped?: boolean;
  weight?: 2 | 3 | 4;
};

export const DescriptionList = ({
  children,
  margin = false,
  pending = false,
  striped = false,
  weight = 3,
}: DescriptionListProps) => (
  <dl
    className={clsx(styles.descriptionList, {
      [Classes.SKELETON]: pending,
      [styles.noMargin]: !margin,
      [styles.striped]: striped,
      [styles.weight2]: weight == 2,
      [styles.weight3]: weight == 3,
      [styles.weight4]: weight == 4,
    })}
  >
    {children}
  </dl>
);
