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

import { AnchorButton, Button, ButtonGroup, Card } from '@blueprintjs/core';

import { ConfirmationButton } from '@/components/ConfirmationButton';
import { NavButton } from '@/components/NavButton';

import { useActiveDeployment } from '../../api/getActiveDeployment';
import { useStandUpAwsDeployment } from '../../api/standUpAwsDeployment';
import { useStandUpLocalDeployment } from '../../api/standUpLocalDeployment';
import { useStartRaceApps } from '../../api/startRaceApps';
import { useStopRaceApps } from '../../api/stopRaceApps';
import { useTearDownAwsDeployment } from '../../api/tearDownAwsDeployment';
import { useTearDownLocalDeployment } from '../../api/tearDownLocalDeployment';
import { DeploymentMode } from '../../types';

import styles from './DeploymentActionsSummary.module.css';

const getStandUpHook = (mode: DeploymentMode) => {
  if (mode == 'aws') {
    return useStandUpAwsDeployment;
  }
  return useStandUpLocalDeployment;
};

const getTearDownHook = (mode: DeploymentMode) => {
  if (mode == 'aws') {
    return useTearDownAwsDeployment;
  }
  return useTearDownLocalDeployment;
};

type DeploymentActionsSummaryProps = {
  mode: DeploymentMode;
  name: string;
};

export const DeploymentActionsSummary = ({ mode, name }: DeploymentActionsSummaryProps) => {
  const { data: activeDeployment } = useActiveDeployment({ mode });
  const otherDeploymentActive = activeDeployment?.name ? activeDeployment.name != name : false;
  const thisDeploymentActive = name == activeDeployment?.name;

  const standUp = getStandUpHook(mode)();
  const handleStandUp = () =>
    standUp.mutate({ data: { force: false, nodes: null, no_publish: false, timeout: 300 }, name });

  const start = useStartRaceApps();
  const handleStart = () =>
    start.mutate({ data: { force: false, nodes: null, timeout: 300 }, mode, name });

  const stop = useStopRaceApps();
  const handleStop = () =>
    stop.mutate({ data: { force: false, nodes: null, timeout: 300 }, mode, name });

  const tearDown = getTearDownHook(mode)();
  const handleTearDown = () =>
    tearDown.mutate({ data: { force: false, nodes: null, timeout: 300 }, name });
  const handleForceTearDown = () =>
    tearDown.mutate({ data: { force: true, nodes: null, timeout: 300 }, name });

  return (
    <Card className={styles.actions}>
      <Button
        className={styles.large}
        disabled={otherDeploymentActive}
        onClick={handleStandUp}
        text="Stand Up Deployment"
      />
      <Button
        className={styles.large}
        disabled={!thisDeploymentActive}
        onClick={handleStart}
        text="Start RACE Apps"
      />
      <Button
        className={styles.large}
        disabled={!thisDeploymentActive}
        onClick={handleStop}
        text="Stop RACE Apps"
      />
      <ButtonGroup className={styles.large}>
        <Button
          disabled={!thisDeploymentActive}
          fill
          onClick={handleTearDown}
          text="Tear Down Deployment"
        />
        <ConfirmationButton
          alertProps={{
            cancelButtonText: 'Cancel',
            intent: 'danger',
          }}
          disabled={!thisDeploymentActive}
          icon="high-priority"
          onClick={handleForceTearDown}
          prompt="Are you sure you want to forcefully tear down the deployment?"
        />
      </ButtonGroup>
      <NavButton
        className={styles.large}
        disabled={!thisDeploymentActive}
        text={'Get Messages'}
        to={`/deployments/${mode}/${name}/messages/list`}
      ></NavButton>
      <NavButton
        className={styles.small}
        disabled={!thisDeploymentActive}
        text={'Send Auto Messages'}
        to={`/deployments/${mode}/${name}/messages/send-auto`}
      ></NavButton>
      <NavButton
        className={styles.small}
        disabled={!thisDeploymentActive}
        text={'Send Manual Messages'}
        to={`/deployments/${mode}/${name}/messages/send-manual`}
      ></NavButton>
      <AnchorButton
        className={styles.small}
        disabled={!thisDeploymentActive}
        href={`${window.location.protocol}//${window.location.hostname}:16686`}
        rightIcon="arrow-right"
        target="_blank"
        text="OpenTracing"
      />
      <AnchorButton
        className={styles.small}
        disabled={!thisDeploymentActive}
        href={`${window.location.protocol}//${window.location.hostname}:6080`}
        rightIcon="arrow-right"
        target="_blank"
        text="Network Visualization"
      />
    </Card>
  );
};
