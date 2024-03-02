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

import { Spinner } from '@blueprintjs/core';

import { useQueuedOperation } from '../../api/getQueuedOperation';
import { LiveLogWindow } from '../LiveLogWindow';
import { OfflineLogWindow } from '../OfflineLogWindow';
import { OperationFacts } from '../OperationFacts';

import styles from './OperationDetails.module.css';

type OperationDetailsProps = {
  id: number;
};

export const OperationDetails = ({ id }: OperationDetailsProps) => {
  const query = useQueuedOperation({ id });

  return (
    <div className={styles.details}>
      <div className={styles.logs}>
        {query.isLoading && <Spinner />}
        {query.data &&
          (query.data.state == 'PENDING' || query.data.state == 'RUNNING' ? (
            <LiveLogWindow id={id} />
          ) : (
            <OfflineLogWindow id={id} />
          ))}
      </div>
      <div>
        <div className={styles.facts}>
          {query.isLoading && <Spinner />}
          {query.data && <OperationFacts operation={query.data} />}
        </div>
      </div>
    </div>
  );
};
