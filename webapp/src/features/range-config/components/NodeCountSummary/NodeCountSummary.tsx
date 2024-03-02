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

import { Card, Elevation } from '@blueprintjs/core';

import { NodeCounts } from '../../types';

import styles from './NodeCountSummary.module.css';

type NodeCountSummaryProps = {
  counts: NodeCounts;
};

export const NodeCountSummary = ({ counts }: NodeCountSummaryProps) => (
  <div className={styles.summary}>
    <Card className={styles.count} elevation={Elevation.TWO}>
      <span>Clients:</span>
      <span>{counts.type.client}</span>

      <span>Servers:</span>
      <span>{counts.type.server}</span>
    </Card>

    <Card className={styles.count} elevation={Elevation.TWO}>
      <span>Android:</span>
      <span>{counts.platform.android}</span>

      <span>Linux:</span>
      <span>{counts.platform.linux}</span>
    </Card>

    <Card className={styles.count} elevation={Elevation.TWO}>
      <span>Genesis:</span>
      <span>{counts.genesis.true}</span>

      <span>Non-Genesis:</span>
      <span>{counts.genesis.false}</span>
    </Card>

    <Card className={styles.count} elevation={Elevation.TWO}>
      <span>Bridged:</span>
      <span>{counts.bridge.true}</span>

      <span>Managed:</span>
      <span>{counts.bridge.false}</span>
    </Card>
  </div>
);
