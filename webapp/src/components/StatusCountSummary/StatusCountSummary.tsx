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
import { Fragment } from 'react';

import styles from './StatusCountSummary.module.css';

export type StatusCountSummaryProps<T extends string> = {
  counts: Record<T, number>;
  isLoading?: boolean;
  labels: Record<T, string>;
  total: number;
};

export const StatusCountSummary = <T extends string>({
  counts,
  isLoading = false,
  labels,
  total,
}: StatusCountSummaryProps<T>) => (
  <div className={clsx(styles.summary, { [Classes.SKELETON]: isLoading })}>
    {Object.entries(counts).map(([key, count]) => (
      <Fragment key={key}>
        <span className={clsx(styles.count, { [styles.zero]: count == 0 })}>
          {`${count}/${total}`}
        </span>
        <span className={clsx({ [styles.zero]: count == 0 })}>{labels[key as T]}</span>
      </Fragment>
    ))}
  </div>
);
