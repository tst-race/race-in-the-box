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

import {
  StateBox,
  StateTransition,
  StateVisualizationCanvas,
} from '@/features/state-visualization';

import { NodeActions, NodeStatus } from '../../types';
import { NodeStatusColors } from '../../utils/nodeStatusColors';

import styles from './NodeStateVisualization.module.css';

const STATE_WIDTH = 80;
const STATE_GAP = 10;
const SLOT_WIDTH = 16;
const BORDER_WIDTH = 3;

const TRN_HEIGHT = 25;
const STATE_Y_POS = 2 * TRN_HEIGHT;
const INV_TRN_Y_POS = STATE_Y_POS + 75;

/** Calculate x-pos for a given state/slot index */
const calcXPos = (stateIndex: number, slot = 0): number =>
  stateIndex * (STATE_WIDTH + STATE_GAP) + slot * SLOT_WIDTH - (slot > 0 ? 1 : 0);

/** Calculate width of a transition using the left and right states/slot indices */
const calcWidth = (
  leftState: number,
  leftSlot: number,
  rightState: number,
  rightSlot: number
): number =>
  (rightState - leftState) * (STATE_WIDTH + STATE_GAP) +
  (rightSlot - leftSlot) * SLOT_WIDTH +
  BORDER_WIDTH;

// Indexes of state boxes
const READY_TO_GEN_CONF = 0;
const READY_TO_TAR_CONF = 1;
const DOWN = 2;
const READY_TO_PUBLIC_CONF = 3;
const READY_TO_INSTALL_CONF = 4;
const READY_TO_BOOTSTRAP = 5;
const READY_TO_START = 6;
const INITIALIZING = 7;
const RUNNING = 8;
const STOPPED = 9;
const ERROR = 10;
const UNKNOWN = 11;

type NodeStateVisualizationProps = NodeActions & {
  allStatuses: NodeStatus[];
  canBootstrap: boolean;
  enableAllActions: boolean;
  filters: Record<string, string>;
  force: boolean;
  numSelected: number;
  onlyStatus: NodeStatus | null;
  setFilters?: (filters: Record<string, string>) => void;
};

export const NodeStateVisualization = ({
  allStatuses,
  canBootstrap,
  enableAllActions,
  filters,
  force,
  numSelected,
  onlyStatus,
  onBootstrap,
  onClear,
  onGenerateConfigs,
  onInstallConfigs,
  onPublishConfigs,
  onReset,
  onStart,
  onStop,
  onTarConfigs,
  onTearDown,
  onStandUp,
  setFilters,
}: NodeStateVisualizationProps) => {
  const createOnClickFilter = (status: NodeStatus) =>
    setFilters
      ? () => {
          if (filters['status'] == status) {
            setFilters({});
          } else {
            setFilters({ status });
          }
        }
      : undefined;

  return (
    <div className={styles.nodeState}>
      <StateVisualizationCanvas>
        <StateBox
          name="Ready To Generate Configs"
          color={NodeStatusColors['READY_TO_GENERATE_CONFIG']}
          disabled={!allStatuses?.includes('READY_TO_GENERATE_CONFIG')}
          onClick={createOnClickFilter('READY_TO_GENERATE_CONFIG')}
          xPos={calcXPos(READY_TO_GEN_CONF)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Ready To Create Config Archive"
          color={NodeStatusColors['READY_TO_TAR_CONFIGS']}
          disabled={!allStatuses?.includes('READY_TO_TAR_CONFIGS')}
          onClick={createOnClickFilter('READY_TO_TAR_CONFIGS')}
          xPos={calcXPos(READY_TO_TAR_CONF)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Down"
          color={NodeStatusColors['DOWN']}
          disabled={!allStatuses?.includes('DOWN')}
          onClick={createOnClickFilter('DOWN')}
          xPos={calcXPos(DOWN)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Ready To Publish Configs"
          color={NodeStatusColors['READY_TO_PUBLISH_CONFIGS']}
          disabled={!allStatuses?.includes('READY_TO_PUBLISH_CONFIGS')}
          onClick={createOnClickFilter('READY_TO_PUBLISH_CONFIGS')}
          xPos={calcXPos(READY_TO_PUBLIC_CONF)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Ready To Install Configs"
          color={NodeStatusColors['READY_TO_INSTALL_CONFIGS']}
          disabled={!allStatuses?.includes('READY_TO_INSTALL_CONFIGS')}
          onClick={createOnClickFilter('READY_TO_INSTALL_CONFIGS')}
          xPos={calcXPos(READY_TO_INSTALL_CONF)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Ready To Bootstrap"
          color={NodeStatusColors['READY_TO_BOOTSTRAP']}
          disabled={!allStatuses?.includes('READY_TO_BOOTSTRAP')}
          onClick={createOnClickFilter('READY_TO_BOOTSTRAP')}
          xPos={calcXPos(READY_TO_BOOTSTRAP)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Ready To Start"
          color={NodeStatusColors['READY_TO_START']}
          disabled={!allStatuses?.includes('READY_TO_START')}
          onClick={createOnClickFilter('READY_TO_START')}
          xPos={calcXPos(READY_TO_START)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Initializing"
          color={NodeStatusColors['INITIALIZING']}
          disabled={!allStatuses?.includes('INITIALIZING')}
          onClick={createOnClickFilter('INITIALIZING')}
          xPos={calcXPos(INITIALIZING)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Running"
          color={NodeStatusColors['RUNNING']}
          disabled={!allStatuses?.includes('RUNNING')}
          onClick={createOnClickFilter('RUNNING')}
          xPos={calcXPos(RUNNING)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Stopped"
          color={NodeStatusColors['STOPPED']}
          disabled={!allStatuses?.includes('STOPPED')}
          onClick={createOnClickFilter('STOPPED')}
          xPos={calcXPos(STOPPED)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Error"
          color={NodeStatusColors['ERROR']}
          disabled={!allStatuses?.includes('ERROR')}
          onClick={createOnClickFilter('ERROR')}
          xPos={calcXPos(ERROR)}
          yPos={STATE_Y_POS}
        />
        <StateBox
          name="Unknown"
          color={NodeStatusColors['UNKNOWN']}
          disabled={!allStatuses?.includes('UNKNOWN')}
          onClick={createOnClickFilter('UNKNOWN')}
          xPos={calcXPos(UNKNOWN)}
          yPos={STATE_Y_POS}
        />

        <StateTransition
          name="Generate Configs"
          color={NodeStatusColors['READY_TO_GENERATE_CONFIG']}
          disabled={onlyStatus != 'READY_TO_GENERATE_CONFIG' && !force}
          onClick={() => onGenerateConfigs(force, false)}
          height={enableAllActions ? 2 * TRN_HEIGHT : TRN_HEIGHT}
          width={calcWidth(READY_TO_GEN_CONF, 1, DOWN, 2)}
          xPos={calcXPos(READY_TO_GEN_CONF, 1)}
          yPos={enableAllActions ? 0 : TRN_HEIGHT}
        />
        {enableAllActions && (
          <>
            <StateTransition
              name="Gen"
              color={NodeStatusColors['READY_TO_TAR_CONFIGS']}
              disabled={onlyStatus != 'READY_TO_GENERATE_CONFIG' && !force}
              onClick={() => onGenerateConfigs(force, true)}
              height={TRN_HEIGHT}
              width={calcWidth(READY_TO_GEN_CONF, 2, READY_TO_TAR_CONF, 1)}
              xPos={calcXPos(READY_TO_GEN_CONF, 2)}
              yPos={TRN_HEIGHT}
            />
            <StateTransition
              name="Archive"
              color={NodeStatusColors['READY_TO_TAR_CONFIGS']}
              disabled={onlyStatus != 'READY_TO_TAR_CONFIGS' && !force}
              onClick={() => onTarConfigs(force)}
              height={TRN_HEIGHT}
              width={calcWidth(READY_TO_TAR_CONF, 2, DOWN, 1)}
              xPos={calcXPos(READY_TO_TAR_CONF, 2)}
              yPos={TRN_HEIGHT}
            />
          </>
        )}
        <StateTransition
          name="Stand Up"
          color={NodeStatusColors[canBootstrap ? 'READY_TO_BOOTSTRAP' : 'READY_TO_START']}
          disabled={onlyStatus != 'DOWN' && !force}
          onClick={() => onStandUp(force, false)}
          height={enableAllActions ? 2 * TRN_HEIGHT : TRN_HEIGHT}
          width={calcWidth(DOWN, 3, canBootstrap ? READY_TO_BOOTSTRAP : READY_TO_START, 2)}
          xPos={calcXPos(DOWN, 3)}
          yPos={enableAllActions ? 0 : TRN_HEIGHT}
        />
        {enableAllActions && (
          <>
            <StateTransition
              name="Up"
              color={NodeStatusColors['READY_TO_PUBLISH_CONFIGS']}
              disabled={onlyStatus != 'DOWN' && !force}
              onClick={() => onStandUp(force, true)}
              height={TRN_HEIGHT}
              width={calcWidth(DOWN, 4, READY_TO_PUBLIC_CONF, 2)}
              xPos={calcXPos(DOWN, 4)}
              yPos={TRN_HEIGHT}
            />
            <StateTransition
              name="Pub"
              color={NodeStatusColors['READY_TO_INSTALL_CONFIGS']}
              disabled={onlyStatus != 'READY_TO_PUBLISH_CONFIGS' && !force}
              onClick={() => onPublishConfigs(force)}
              height={TRN_HEIGHT}
              width={calcWidth(READY_TO_PUBLIC_CONF, 3, READY_TO_INSTALL_CONF, 1)}
              xPos={calcXPos(READY_TO_PUBLIC_CONF, 3)}
              yPos={TRN_HEIGHT}
            />
            <StateTransition
              name="Install"
              color={NodeStatusColors[canBootstrap ? 'READY_TO_BOOTSTRAP' : 'READY_TO_START']}
              disabled={onlyStatus != 'READY_TO_INSTALL_CONFIGS' && !force}
              onClick={() => onInstallConfigs(force)}
              height={TRN_HEIGHT}
              width={calcWidth(
                READY_TO_INSTALL_CONF,
                2,
                canBootstrap ? READY_TO_BOOTSTRAP : READY_TO_START,
                1
              )}
              xPos={calcXPos(READY_TO_INSTALL_CONF, 2)}
              yPos={TRN_HEIGHT}
            />
          </>
        )}
        {canBootstrap && (
          <StateTransition
            name="Bootstrap"
            color={NodeStatusColors['READY_TO_START']}
            disabled={numSelected != 1 || (onlyStatus != 'READY_TO_BOOTSTRAP' && !force)}
            onClick={() => onBootstrap(force)}
            height={TRN_HEIGHT}
            width={calcWidth(READY_TO_BOOTSTRAP, 3, READY_TO_START, 3)}
            xPos={calcXPos(READY_TO_BOOTSTRAP, 3)}
            yPos={TRN_HEIGHT}
          />
        )}
        <StateTransition
          name="Start"
          color={NodeStatusColors['RUNNING']}
          disabled={onlyStatus != 'READY_TO_START' && !force}
          onClick={() => onStart(force)}
          height={TRN_HEIGHT}
          width={calcWidth(READY_TO_START, 4, RUNNING, 1)}
          xPos={calcXPos(READY_TO_START, 4)}
          yPos={TRN_HEIGHT}
        />
        <StateTransition
          name="Stop"
          color={NodeStatusColors['STOPPED']}
          disabled={onlyStatus != 'RUNNING' && !force}
          onClick={() => onStop(force)}
          height={2 * TRN_HEIGHT}
          width={calcWidth(RUNNING, 2, STOPPED, 4)}
          xPos={calcXPos(RUNNING, 2)}
        />
        <StateTransition
          name="Restart"
          color={NodeStatusColors['RUNNING']}
          disabled={onlyStatus != 'STOPPED' && !force}
          onClick={() => onStart(force)}
          reverse
          height={TRN_HEIGHT}
          width={calcWidth(RUNNING, 3, STOPPED, 3)}
          xPos={calcXPos(RUNNING, 3)}
          yPos={TRN_HEIGHT}
        />
        <StateTransition
          name="Stop"
          color={NodeStatusColors['STOPPED']}
          disabled={onlyStatus != 'INITIALIZING' && !force}
          onClick={() => onStop(force)}
          inverted
          height={TRN_HEIGHT}
          width={calcWidth(INITIALIZING, 1, STOPPED, 1)}
          xPos={calcXPos(INITIALIZING, 1)}
          yPos={INV_TRN_Y_POS}
        />
        {enableAllActions && (
          <>
            <StateTransition
              name="Reset"
              color={NodeStatusColors[canBootstrap ? 'READY_TO_BOOTSTRAP' : 'READY_TO_START']}
              disabled={onlyStatus != 'STOPPED' && !force}
              onClick={() => onReset(force)}
              inverted
              reverse
              height={2 * TRN_HEIGHT}
              width={calcWidth(canBootstrap ? READY_TO_BOOTSTRAP : READY_TO_START, 1, STOPPED, 2)}
              xPos={calcXPos(canBootstrap ? READY_TO_BOOTSTRAP : READY_TO_START, 1)}
              yPos={INV_TRN_Y_POS}
            />
            <StateTransition
              name="Clear"
              color={NodeStatusColors['READY_TO_PUBLISH_CONFIGS']}
              disabled={onlyStatus != 'STOPPED' && !force}
              onClick={() => onClear(force)}
              inverted
              reverse
              height={3 * TRN_HEIGHT}
              width={calcWidth(READY_TO_PUBLIC_CONF, 1, STOPPED, 3)}
              xPos={calcXPos(READY_TO_PUBLIC_CONF, 1)}
              yPos={INV_TRN_Y_POS}
            />
          </>
        )}
        <StateTransition
          name="Tear Down"
          color={NodeStatusColors['DOWN']}
          disabled={onlyStatus != 'STOPPED' && !force}
          onClick={() => onTearDown(force)}
          inverted
          reverse
          height={enableAllActions ? 4 * TRN_HEIGHT : 2 * TRN_HEIGHT}
          width={calcWidth(DOWN, 3, STOPPED, 4)}
          xPos={calcXPos(DOWN, 3)}
          yPos={INV_TRN_Y_POS}
        />
        <StateTransition
          name="Tear Down"
          color={NodeStatusColors['DOWN']}
          disabled={onlyStatus != 'ERROR' && !force}
          onClick={() => onTearDown(force)}
          inverted
          reverse
          height={enableAllActions ? 5 * TRN_HEIGHT : 3 * TRN_HEIGHT}
          width={calcWidth(DOWN, 2, ERROR, 1)}
          xPos={calcXPos(DOWN, 2)}
          yPos={INV_TRN_Y_POS}
        />
        <StateTransition
          name="Tear Down"
          color={NodeStatusColors['DOWN']}
          disabled={onlyStatus != 'UNKNOWN' && !force}
          onClick={() => onTearDown(force)}
          inverted
          reverse
          height={enableAllActions ? 6 * TRN_HEIGHT : 4 * TRN_HEIGHT}
          width={calcWidth(DOWN, 1, UNKNOWN, 1)}
          xPos={calcXPos(DOWN, 1)}
          yPos={INV_TRN_Y_POS}
        />
      </StateVisualizationCanvas>
    </div>
  );
};
