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

import { AlertProps, IntentProps } from '@blueprintjs/core';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { getToaster } from '@/lib/toaster';
import { OperationQueuedResult } from '@/types';

import { useArchiveNodeConfigs } from '../api/archiveNodeConfigs';
import { useClearNodeConfigs } from '../api/clearNodeConfigs';
import { useInstallNodeConfigs } from '../api/installNodeConfigs';
import { usePublishNodeConfigs } from '../api/publishNodeConfigs';
import { useResetNodes } from '../api/resetNodes';
import { useStandUpAwsDeployment } from '../api/standUpAwsDeployment';
import { useStandUpLocalDeployment } from '../api/standUpLocalDeployment';
import { useStartRaceApps } from '../api/startRaceApps';
import { useStopRaceApps } from '../api/stopRaceApps';
import { useTearDownAwsDeployment } from '../api/tearDownAwsDeployment';
import { useTearDownLocalDeployment } from '../api/tearDownLocalDeployment';
import { NodeAggregate, NodeActions, NodeStatus, DeploymentMode } from '../types';

const pluralizeNodes = (nodeNames: string[] | null) => {
  if (!nodeNames) {
    return 'all nodes';
  }
  if (nodeNames.length == 1) {
    return '1 node';
  }
  return `${nodeNames.length} nodes`;
};

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

type UseNodeActionsOptions = {
  mode: DeploymentMode;
  name: string;
  nodes: NodeAggregate[];
  selection: number[]; // Selected indices
};

type UseNodeActionsResult = {
  actions: NodeActions;
  allStatuses: NodeStatus[];
  canBootstrap: boolean;
  confirmAlertProps: AlertProps;
  onlyStatus: NodeStatus | null;
};

type ConfirmActionPrompt = IntentProps & {
  action: () => void;
  message: string;
};

export const useNodeActions = ({
  mode,
  name,
  nodes,
  selection,
}: UseNodeActionsOptions): UseNodeActionsResult => {
  const selectedNodes =
    selection.length == 0 ? nodes : nodes.filter((node, index) => selection.includes(index));

  const statusSet = new Set<NodeStatus | undefined>();
  const genesisSet = new Set<boolean | undefined>();

  for (const node of selectedNodes) {
    statusSet.add(node.nodeStatus?.status);
    genesisSet.add(node.config?.genesis);
  }

  const allStatuses: NodeStatus[] = [];
  statusSet.forEach((status) => {
    if (status != undefined) {
      allStatuses.push(status);
    }
  });

  // We can allow bootstrap actions only when all selected nodes are non-genesis
  const canBootstrap = genesisSet.size == 1 && genesisSet.has(false);
  const onlyStatus = allStatuses.length == 1 ? allStatuses[0] : null;

  const actionTargetNodes = selectedNodes ? selectedNodes.map((node) => node.name) : null;

  const [confirm, setConfirm] = useState<ConfirmActionPrompt | null>(null);

  const archiveConfigs = useArchiveNodeConfigs();
  const standUp = getStandUpHook(mode)();
  const publishConfigs = usePublishNodeConfigs();
  const installConfigs = useInstallNodeConfigs();
  const startApps = useStartRaceApps();
  const stopApps = useStopRaceApps();
  const clearConfigs = useClearNodeConfigs();
  const resetNodes = useResetNodes();
  const tearDown = getTearDownHook(mode)();

  const navigate = useNavigate();

  // Show a success toast with a link to the queued operation
  const showToast = (message: string) => (result: OperationQueuedResult) =>
    getToaster().show({
      intent: 'success',
      message: (
        <Link to={`/operations/${result.id}`}>
          {message} {pluralizeNodes(actionTargetNodes)} (operation {result.id})
        </Link>
      ),
    });

  // Wrap a node action so that the user must confirm it first if it is a forced action
  const confirmAction =
    (
      message: string,
      action: (force: boolean, partial?: boolean) => void,
      intent: IntentProps['intent'] = 'primary'
    ) =>
    (force: boolean, partial?: boolean) => {
      if (force) {
        setConfirm({
          action: () => {
            action(force, partial);
            setConfirm(null);
          },
          intent,
          message,
        });
      } else {
        action(force, partial);
      }
    };

  return {
    actions: {
      onBootstrap: (force) => {
        if (actionTargetNodes && actionTargetNodes.length == 1) {
          navigate(`../bootstrap-node?target=${actionTargetNodes[0]}&force=${force}`);
        } else {
          getToaster().show({
            intent: 'warning',
            message: 'Must select a single node to bootstrap',
          });
        }
      },
      onClear: confirmAction(
        'Are you sure you want to forcefully clear configs from the selected nodes?',
        (force) =>
          clearConfigs.mutate(
            {
              name,
              mode,
              data: {
                force,
                nodes: actionTargetNodes,
                timeout: 300,
              },
            },
            {
              onSuccess: showToast('Clearing configs for'),
            }
          )
      ),
      onGenerateConfigs: (force, partial) =>
        navigate(`../generate-config?force=${force}&skip_archive=${partial}`),
      onInstallConfigs: confirmAction(
        'Are you sure you want to overwrite configs that may already be installed on the selected nodes?',
        (force) =>
          installConfigs.mutate(
            {
              name,
              mode,
              data: {
                force,
                nodes: actionTargetNodes,
                timeout: 300,
              },
            },
            {
              onSuccess: showToast('Installing configs for'),
            }
          )
      ),
      onPublishConfigs: confirmAction(
        'Are you sure you want to overwrite configs that may already be published to the file server?',
        (force) =>
          publishConfigs.mutate(
            {
              name,
              mode,
              data: {
                force,
                nodes: actionTargetNodes,
                timeout: 300,
              },
            },
            {
              onSuccess: showToast('Publishing configs for'),
            }
          )
      ),
      onReset: confirmAction(
        'Are you sure you want to forcefully reset the selected nodes?',
        (force) =>
          resetNodes.mutate(
            {
              name,
              mode,
              data: {
                force,
                nodes: actionTargetNodes,
                timeout: 300,
              },
            },
            {
              onSuccess: showToast('Resetting'),
            }
          )
      ),
      onStandUp: confirmAction(
        'Are you sure you want to forcefully stand up the selected nodes?',
        (force, no_publish = false) =>
          standUp.mutate(
            {
              name,
              data: {
                force,
                nodes: actionTargetNodes,
                no_publish,
                timeout: 300,
              },
            },
            {
              onSuccess: showToast('Standing up'),
            }
          )
      ),
      onStart: confirmAction(
        'Are you sure you want to forcefully start the selected nodes?',
        (force) =>
          startApps.mutate(
            {
              name,
              mode,
              data: {
                force,
                nodes: actionTargetNodes,
                timeout: 300,
              },
            },
            {
              onSuccess: showToast('Starting'),
            }
          )
      ),
      onStop: confirmAction(
        'Are you sure you want to forcefully stop the selected nodes?',
        (force) =>
          stopApps.mutate(
            {
              name,
              mode,
              data: {
                force,
                nodes: actionTargetNodes,
                timeout: 300,
              },
            },
            {
              onSuccess: showToast('Stopping'),
            }
          )
      ),
      onTarConfigs: confirmAction(
        'Are you sure you want to overwrite config archives that may already exist?',
        (force) =>
          archiveConfigs.mutate(
            {
              name,
              mode,
              data: {
                force,
                nodes: actionTargetNodes,
                timeout: 300,
              },
            },
            {
              onSuccess: showToast('Creating config archives for'),
            }
          )
      ),
      onTearDown: confirmAction(
        'Are you sure you want to forcefully tear down the selected nodes?',
        (force) =>
          tearDown.mutate(
            {
              name,
              data: {
                force,
                nodes: actionTargetNodes,
                timeout: 300,
              },
            },
            {
              onSuccess: showToast('Tearing down'),
            }
          ),
        'danger'
      ),
    },
    allStatuses,
    canBootstrap,
    confirmAlertProps: {
      cancelButtonText: 'Cancel',
      canEscapeKeyCancel: true,
      canOutsideClickCancel: true,
      children: confirm?.message,
      intent: confirm?.intent,
      isOpen: confirm != null,
      onCancel: () => setConfirm(null),
      onConfirm: confirm?.action,
    },
    onlyStatus,
  };
};
