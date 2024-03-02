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

import { Icon } from '@blueprintjs/core';
import { Tooltip2 } from '@blueprintjs/popover2';
import { formatDistanceToNow } from 'date-fns';

import { toDate } from '@/utils/toDate';

import styles from './OperationStopped.module.css';

type OperationStoppedProps = {
  displayType?: 'absolute' | 'relative';
  stoppedTime: string | null;
};

export const OperationStopped = ({
  displayType = 'relative',
  stoppedTime,
}: OperationStoppedProps) => (
  <div className={styles.stopped}>
    {stoppedTime != null && (
      <>
        <Icon icon="calendar" size={12} />
        {displayType == 'absolute' ? (
          <span>{stoppedTime}</span>
        ) : (
          <Tooltip2 content={stoppedTime} hoverOpenDelay={500}>
            <span>{`${formatDistanceToNow(toDate(stoppedTime))} ago`}</span>
          </Tooltip2>
        )}
      </>
    )}
  </div>
);
