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
import { ReactNode } from 'react';

import styles from './Grid.module.css';

export const spanCol1and2ClassName = styles.spanCol1and2;
export const spanCol2and3ClassName = styles.spanCol2and3;
export const spanCol1and3ClassName = styles.spanCol1and3;

export type GridProps = {
  children: ReactNode;
  numCol: 2 | 3;
};

export const Grid = ({ children, numCol }: GridProps) => (
  <div
    className={clsx(styles.grid, {
      [styles.twoCol]: numCol == 2,
      [styles.threeCol]: numCol == 3,
    })}
  >
    {children}
  </div>
);
