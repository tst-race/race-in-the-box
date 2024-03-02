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

import { Button, Checkbox, Classes, HTMLTable, Spinner, SpinnerSize } from '@blueprintjs/core';
import { Classes as PopoverClasses, Popover2 } from '@blueprintjs/popover2';
import { ReactNode } from 'react';

import { StateTag } from '@/features/state-visualization';
import { UseMultiRowSelectResult } from '@/hooks/useMultiRowSelect';

import { UseDeploymentNodesResult } from '../../hooks/useDeploymentNodes';
import { ContainerStatusValues, NodeStatusReport, NodeStatusValues } from '../../types';
import { ContainerStatusColors } from '../../utils/containerStatusColors';
import { NodeStatusColors } from '../../utils/nodeStatusColors';
import { NodeStatusDescriptionList } from '../NodeStatusDescriptionList';

import styles from './NodeTable.module.css';

const TableCell = ({ children }: { children?: ReactNode }) => (
  <td>{children ? children : <Spinner size={SpinnerSize.SMALL} />}</td>
);

const NodeStatusButton = ({ status }: { status: NodeStatusReport }) => (
  <Popover2
    content={<NodeStatusDescriptionList status={status} />}
    hasBackdrop
    placement="bottom-start"
    popoverClassName={PopoverClasses.POPOVER2_CONTENT_SIZING}
  >
    <Button
      minimal
      onMouseDown={(event) => event.stopPropagation()}
      rightIcon="chevron-right"
      small
      text="Details"
    />
  </Popover2>
);

type NodeTableProps = {
  isLoading: UseDeploymentNodesResult['isLoading'];
  nodes: UseDeploymentNodesResult['nodes'];
  omitContainers?: boolean;
  selection: UseMultiRowSelectResult['selection'];
  setSelection: UseMultiRowSelectResult['setSelection'];
  trProps: UseMultiRowSelectResult['trProps'];
};

export const NodeTable = ({
  isLoading,
  nodes,
  omitContainers = false,
  selection,
  setSelection,
  trProps,
}: NodeTableProps) => (
  <HTMLTable condensed interactive striped>
    <thead>
      <tr>
        <th>
          <Checkbox
            className={styles.selectCheckbox}
            checked={selection.length == nodes.length}
            indeterminate={selection.length > 0 && selection.length != nodes.length}
            label="Select all"
            onChange={(event) =>
              event.currentTarget.checked
                ? setSelection([...Array(nodes.length).keys()])
                : setSelection([])
            }
          />
        </th>
        <th>Name</th>
        {!omitContainers && <th>Container Status</th>}
        <th>Node Status</th>
        <th />
      </tr>
    </thead>
    <tbody>
      {isLoading && (
        <tr>
          <td className={Classes.SKELETON}>Select</td>
          <td className={Classes.SKELETON}>Name</td>
          <td className={Classes.SKELETON}>Container Status</td>
          <td className={Classes.SKELETON}>Node Status</td>
          <td className={Classes.SKELETON}>Details</td>
        </tr>
      )}
      {nodes.map((node, index) => (
        <tr key={node.name} {...trProps}>
          <td>
            <Checkbox className={styles.selectCheckbox} checked={selection.includes(index)} />
          </td>
          <td>{node.name}</td>
          {!omitContainers &&
            (node.config?.bridge ? (
              <td>
                <StateTag>N/A</StateTag>
              </td>
            ) : (
              <TableCell>
                {node.containerStatus && (
                  <StateTag color={ContainerStatusColors[node.containerStatus.status]}>
                    {ContainerStatusValues[node.containerStatus.status]}
                  </StateTag>
                )}
              </TableCell>
            ))}
          <TableCell>
            {node.nodeStatus && (
              <StateTag color={NodeStatusColors[node.nodeStatus.status]}>
                {NodeStatusValues[node.nodeStatus.status]}
              </StateTag>
            )}
          </TableCell>
          <td className={styles.buttonCell}>
            {node.nodeStatus && <NodeStatusButton status={node.nodeStatus} />}
          </td>
        </tr>
      ))}
    </tbody>
  </HTMLTable>
);
