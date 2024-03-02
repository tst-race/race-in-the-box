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

import { Button, Card, Classes, H4 } from '@blueprintjs/core';
import clsx from 'clsx';
import { Fragment } from 'react';
import { useNavigate } from 'react-router-dom';

import { ActionButtons } from '@/components/ActionButtons';

import { useAwsDeploymentConfigSummary } from '../../hooks/useAwsDeploymentConfigSummary';

import styles from './DeploymentConfigSummary.module.css';

export type AwsDeploymentConfigSummaryProps = {
  name: string;
};

export const AwsDeploymentConfigSummary = ({ name }: AwsDeploymentConfigSummaryProps) => {
  const navigate = useNavigate();
  const handleClick = () => navigate('config');

  const { info, isLoading, nodeCounts } = useAwsDeploymentConfigSummary({ name });

  return (
    <Card interactive onClick={handleClick}>
      <H4>Configuration</H4>
      <div className={clsx(styles.summary, { [Classes.SKELETON]: isLoading })}>
        <span className={styles.label}>Client / Server</span>
        <span>{`${nodeCounts.type.client} / ${nodeCounts.type.server}`}</span>

        <span className={styles.label}>Linux / Android</span>
        <span>{`${nodeCounts.platform.linux} / ${nodeCounts.platform.android}`}</span>

        <span className={styles.label}>Genesis / Bootstrapped</span>
        <span>{`${nodeCounts.genesis.true} / ${nodeCounts.genesis.false}`}</span>

        <span className={styles.label}>Managed / Bridged</span>
        <span>{`${nodeCounts.bridge.false} / ${nodeCounts.bridge.true}`}</span>

        {info && (
          <>
            <span className={styles.label}>RACE Core</span>
            <span>{info.config.race_core.raw}</span>

            <span className={styles.label}>Network Manager Plugin</span>
            <span>{info.config.network_manager_kit.name}</span>

            {info.config.comms_channels.map((channel, index) => (
              <Fragment key={channel.name}>
                <span className={styles.label}>{index == 0 ? 'Comms channels' : ''}</span>
                <span>{channel.name}</span>
              </Fragment>
            ))}
          </>
        )}
      </div>
      <ActionButtons noMargin>
        <Button intent="primary" rightIcon="arrow-right" />
      </ActionButtons>
    </Card>
  );
};
