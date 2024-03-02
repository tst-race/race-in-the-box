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

import { Tag, Tree, TreeNodeInfo } from '@blueprintjs/core';
import { produce } from 'immer';
import { useCallback, useReducer } from 'react';
import { FaAndroid, FaDocker, FaLinux, FaMobileAlt, FaServer, FaUser } from 'react-icons/fa';

import { EnclaveClassParams, EnclaveInstanceParams, NodeClassParams, NodeCounts } from '../types';
import { getNodeCountsFromParams } from '../utils/getNodeCountsFromParams';

// -- Types

export type TreeNodeData =
  | { type: 'nodeClasses' }
  | { type: 'nodeClass'; name: string }
  | { type: 'enclaveClasses' }
  | { type: 'enclaveClass'; name: string }
  | { type: 'enclaves' }
  | { type: 'enclave'; index: number };
type TreeNode = TreeNodeInfo<TreeNodeData>;
type TreeNodePath = number[];

export type AddNewForm = 'nodeClass' | 'enclaveClass' | 'enclave';

export type AddEnclaveClassParams = EnclaveClassParams & {
  nodeClasses: Record<string, NodeClassParams>;
};

export type RangeConfigGenerationParametersState = {
  nodeClasses: Record<string, NodeClassParams>;
  enclaveClasses: Record<string, EnclaveClassParams>;
  enclaves: EnclaveInstanceParams[];
  counts: NodeCounts;
  treeNodes: TreeNode[];
  selectedTreeNode: TreeNodeData | null;
  showAddNewForm: AddNewForm | null;
};

export type RangeConfigGenerationParametersAction =
  // Node classes
  | { type: 'ADD_NODE_CLASS'; payload: { name: string; nodeClass: NodeClassParams } }
  | {
      type: 'UPDATE_NODE_CLASS';
      payload: { name: string; oldName?: string; nodeClass: NodeClassParams };
    }
  | { type: 'REMOVE_NODE_CLASS'; payload: { name: string } }
  | { type: 'DUPLICATE_NODE_CLASS'; payload: { name: string } }
  // Enclave classes
  | { type: 'ADD_ENCLAVE_CLASS'; payload: { name: string; enclaveClass: AddEnclaveClassParams } }
  | {
      type: 'UPDATE_ENCLAVE_CLASS';
      payload: { name: string; oldName?: string; enclaveClass: EnclaveClassParams };
    }
  | { type: 'REMOVE_ENCLAVE_CLASS'; payload: { name: string } }
  | { type: 'DUPLICATE_ENCLAVE_CLASS'; payload: { name: string } }
  // Enclave instances
  | { type: 'ADD_ENCLAVE'; payload: { enclave: EnclaveInstanceParams } }
  | { type: 'UPDATE_ENCLAVE'; payload: { index: number; enclave: EnclaveInstanceParams } }
  | { type: 'REMOVE_ENCLAVE'; payload: { index: number } }
  | { type: 'DUPLICATE_ENCLAVE'; payload: { index: number } }
  // Tree operations
  | { type: 'SET_SELECTED'; payload: { treeNodePath: TreeNodePath; isSelected: boolean } }
  | { type: 'SET_EXPANDED'; payload: { treeNodePath: TreeNodePath; isExpanded: boolean } }
  // UI operations
  | { type: 'SHOW_ADD_NEW_FORM'; payload: { addNewForm: AddNewForm } };

export type RangeConfigGenerationParametersMethods = {
  // Node classes
  addNodeClass: (name: string, nodeClass: NodeClassParams) => void;
  updateNodeClass: (name: string, nodeClass: NodeClassParams, oldName?: string) => void;
  removeNodeClass: (name: string) => void;
  duplicateNodeClass: (name: string) => void;
  // Enclave classes
  addEnclaveClass: (name: string, enclaveClass: AddEnclaveClassParams) => void;
  updateEnclaveClass: (name: string, enclaveClass: EnclaveClassParams, oldName?: string) => void;
  removeEnclaveClass: (name: string) => void;
  duplicateEnclaveClass: (name: string) => void;
  // Enclave instances
  addEnclave: (enclave: EnclaveInstanceParams) => void;
  updateEnclave: (index: number, enclave: EnclaveInstanceParams) => void;
  removeEnclave: (index: number) => void;
  duplicateEnclave: (index: number) => void;
  // Tree operations
  handleNodeClick: (treeNode: TreeNode, treeNodePath: TreeNodePath) => void;
  handleNodeCollapse: (treeNode: TreeNode, treeNodePath: TreeNodePath) => void;
  handleNodeExpand: (treeNode: TreeNode, treeNodePath: TreeNodePath) => void;
  // UI operations
  showAddNewForm: (addNewForm: AddNewForm) => void;
};

export type UseRangeConfigGenerationParametersReturn = {
  state: RangeConfigGenerationParametersState;
  methods: RangeConfigGenerationParametersMethods;
};

// -- Functions

const createNodeClassTree = (
  nodeClasses: RangeConfigGenerationParametersState['nodeClasses']
): TreeNode[] =>
  Object.keys(nodeClasses)
    .sort()
    .map(
      (name): TreeNode => ({
        id: `nc-${name}`,
        label: name,
        secondaryLabel: (
          <span>
            {nodeClasses[name].type == 'client' ? <FaUser /> : <FaServer />}
            {nodeClasses[name].platform == 'linux' ? <FaLinux /> : <FaAndroid />}
            {nodeClasses[name].bridge ? <FaMobileAlt /> : <FaDocker />}
          </span>
        ),
        nodeData: { type: 'nodeClass', name },
        hasCaret: false,
        isExpanded: false,
        isSelected: false,
        childNodes: [],
      })
    );

const createEnclaveClassLeaf = (
  name: string,
  enclaveClass: EnclaveClassParams,
  nodeClasses: RangeConfigGenerationParametersState['nodeClasses']
): TreeNode => ({
  id: `ec-${name}`,
  label: name,
  nodeData: { type: 'enclaveClass', name },
  hasCaret: true,
  isExpanded: true,
  isSelected: false,
  childNodes: enclaveClass.nodes.map(
    (instance, index): TreeNode => ({
      id: `ec-${name}-nodes-${index}`,
      label: (
        <>
          <Tag>{instance.nodeQuantity}</Tag>
          {` ${instance.nodeClassName}`}
        </>
      ),
      secondaryLabel: (
        <span>
          {nodeClasses[instance.nodeClassName].type == 'client' ? <FaUser /> : <FaServer />}
          {nodeClasses[instance.nodeClassName].platform == 'linux' ? <FaLinux /> : <FaAndroid />}
          {nodeClasses[instance.nodeClassName].bridge ? <FaMobileAlt /> : <FaDocker />}
        </span>
      ),
      nodeData: { type: 'enclaveClass', name },
      hasCaret: false,
      isExpanded: false,
      isSelected: false,
      childNodes: [],
    })
  ),
});

const createEnclaveClassTree = (
  enclaveClasses: RangeConfigGenerationParametersState['enclaveClasses'],
  nodeClasses: RangeConfigGenerationParametersState['nodeClasses']
): TreeNode[] =>
  Object.keys(enclaveClasses)
    .sort()
    .map((name): TreeNode => createEnclaveClassLeaf(name, enclaveClasses[name], nodeClasses));

const createEnclaveTree = (
  enclaves: RangeConfigGenerationParametersState['enclaves']
): TreeNode[] =>
  enclaves.map(
    (instance, index): TreeNode => ({
      id: `enc-${index}`,
      label: (
        <>
          <Tag>{instance.enclaveQuantity}</Tag>
          {` ${instance.enclaveClassName}`}
        </>
      ),
      nodeData: { type: 'enclave', index },
      hasCaret: false,
      isExpanded: false,
      isSelected: false,
      childNodes: [],
    })
  );

const forEachNode = (treeNodes: TreeNode[] | undefined, callback: (treeNode: TreeNode) => void) => {
  if (treeNodes == undefined) {
    return;
  }
  for (const treeNode of treeNodes) {
    callback(treeNode);
    forEachNode(treeNode.childNodes, callback);
  }
};

const reducer = produce(
  (state: RangeConfigGenerationParametersState, action: RangeConfigGenerationParametersAction) => {
    switch (action.type) {
      // Node classes

      case 'ADD_NODE_CLASS':
        state.nodeClasses[action.payload.name] = action.payload.nodeClass;
        state.treeNodes[0].childNodes = createNodeClassTree(state.nodeClasses);
        if (Object.keys(state.enclaveClasses).length == 1) {
          Object.values(state.enclaveClasses)[0].nodes.push({
            nodeClassName: action.payload.name,
            nodeQuantity: 1,
            portMapping: [],
          });
          state.treeNodes[1].childNodes = createEnclaveClassTree(
            state.enclaveClasses,
            state.nodeClasses
          );
        }
        break;

      case 'UPDATE_NODE_CLASS':
        state.nodeClasses[action.payload.name] = action.payload.nodeClass;
        if (action.payload.oldName != undefined && action.payload.oldName != action.payload.name) {
          delete state.nodeClasses[action.payload.oldName];
          // Handle rename in any enclave classes that referenced the old node class name
          Object.values(state.enclaveClasses).forEach((enclaveClass) => {
            enclaveClass.nodes.forEach((instance) => {
              if (instance.nodeClassName == action.payload.oldName) {
                instance.nodeClassName = action.payload.name;
              }
            });
          });
          state.treeNodes[0].childNodes = createNodeClassTree(state.nodeClasses);
          state.treeNodes[1].childNodes = createEnclaveClassTree(
            state.enclaveClasses,
            state.nodeClasses
          );
          state.selectedTreeNode = null;
        }
        break;

      case 'REMOVE_NODE_CLASS':
        delete state.nodeClasses[action.payload.name];
        // Handle delete in any enclave classes that referenced the node class
        Object.values(state.enclaveClasses).forEach((enclaveClass) => {
          enclaveClass.nodes = enclaveClass.nodes.filter(
            (instance) => instance.nodeClassName != action.payload.name
          );
        });
        state.treeNodes[0].childNodes = createNodeClassTree(state.nodeClasses);
        state.treeNodes[1].childNodes = createEnclaveClassTree(
          state.enclaveClasses,
          state.nodeClasses
        );
        state.selectedTreeNode = null;
        break;

      case 'DUPLICATE_NODE_CLASS': {
        let copyCount = 1;
        while (`${action.payload.name}-${copyCount}` in state.nodeClasses) {
          copyCount += 1;
        }
        const newName = `${action.payload.name}-${copyCount}`;

        state.nodeClasses[newName] = state.nodeClasses[action.payload.name];
        state.treeNodes[0].childNodes = createNodeClassTree(state.nodeClasses);
        state.selectedTreeNode = { type: 'nodeClass', name: newName };
        break;
      }

      // Enclave classes

      case 'ADD_ENCLAVE_CLASS': {
        const { nodeClasses, ...enclaveClass } = action.payload.enclaveClass;
        // Auto-imported node classes
        if (nodeClasses) {
          for (const name in nodeClasses) {
            state.nodeClasses[name] = nodeClasses[name];
          }
          state.treeNodes[0].childNodes = createNodeClassTree(state.nodeClasses);
        }
        state.enclaveClasses[action.payload.name] = enclaveClass;
        state.enclaves.push({
          enclaveClassName: action.payload.name,
          enclaveQuantity: 1,
        });
        state.treeNodes[1].childNodes = createEnclaveClassTree(
          state.enclaveClasses,
          state.nodeClasses
        );
        state.treeNodes[2].childNodes = createEnclaveTree(state.enclaves);
        break;
      }

      case 'UPDATE_ENCLAVE_CLASS': {
        state.enclaveClasses[action.payload.name] = action.payload.enclaveClass;
        if (action.payload.oldName != undefined && action.payload.oldName != action.payload.name) {
          delete state.enclaveClasses[action.payload.oldName];
          // Handle rename in any enclave instances that referenced the old enclave class name
          state.enclaves.forEach((instance) => {
            if (instance.enclaveClassName == action.payload.oldName) {
              instance.enclaveClassName = action.payload.name;
            }
          });
          state.treeNodes[1].childNodes = createEnclaveClassTree(
            state.enclaveClasses,
            state.nodeClasses
          );
          state.treeNodes[2].childNodes = createEnclaveTree(state.enclaves);
          state.selectedTreeNode = null;
        } else {
          // Rebuild just the affected enclave class tree node, rather than the entire subtree
          // (otherwise we lose the user's expanded/collapsed selections)
          state.treeNodes[1].childNodes = state.treeNodes[1].childNodes?.map((treeNode) => {
            if (
              treeNode.nodeData?.type == 'enclaveClass' &&
              treeNode.nodeData.name == action.payload.name
            ) {
              return createEnclaveClassLeaf(
                action.payload.name,
                state.enclaveClasses[action.payload.name],
                state.nodeClasses
              );
            }
            return treeNode;
          });
        }
        break;
      }

      case 'REMOVE_ENCLAVE_CLASS':
        delete state.enclaveClasses[action.payload.name];
        // Handle delete in any enclave instances that referenced the enclave class
        state.enclaves = state.enclaves.filter(
          (instance) => instance.enclaveClassName != action.payload.name
        );
        state.treeNodes[1].childNodes = createEnclaveClassTree(
          state.enclaveClasses,
          state.nodeClasses
        );
        state.treeNodes[2].childNodes = createEnclaveTree(state.enclaves);
        state.selectedTreeNode = null;
        break;

      case 'DUPLICATE_ENCLAVE_CLASS': {
        let copyCount = 1;
        while (`${action.payload.name}-${copyCount}` in state.enclaveClasses) {
          copyCount += 1;
        }
        const newName = `${action.payload.name}-${copyCount}`;

        state.enclaveClasses[newName] = state.enclaveClasses[action.payload.name];
        state.treeNodes[1].childNodes = createEnclaveClassTree(
          state.enclaveClasses,
          state.nodeClasses
        );
        state.selectedTreeNode = { type: 'enclaveClass', name: newName };
        break;
      }

      // Enclave instances

      case 'ADD_ENCLAVE':
        state.enclaves.push(action.payload.enclave);
        state.treeNodes[2].childNodes = createEnclaveTree(state.enclaves);
        break;

      case 'UPDATE_ENCLAVE':
        state.enclaves[action.payload.index] = action.payload.enclave;
        state.treeNodes[2].childNodes = createEnclaveTree(state.enclaves);
        break;

      case 'REMOVE_ENCLAVE':
        state.enclaves.splice(action.payload.index, 1);
        state.treeNodes[2].childNodes = createEnclaveTree(state.enclaves);
        state.selectedTreeNode = null;
        break;

      case 'DUPLICATE_ENCLAVE':
        state.enclaves.splice(action.payload.index, 0, state.enclaves[action.payload.index]);
        state.treeNodes[2].childNodes = createEnclaveTree(state.enclaves);
        state.selectedTreeNode = { type: 'enclave', index: action.payload.index + 1 };
        break;

      // Tree operations

      case 'SET_SELECTED': {
        forEachNode(state.treeNodes, (node) => (node.isSelected = false));
        const treeNode = Tree.nodeFromPath(action.payload.treeNodePath, state.treeNodes);
        treeNode.isSelected = action.payload.isSelected;
        state.selectedTreeNode = null;
        if (action.payload.isSelected) {
          if (treeNode.nodeData != undefined) {
            state.selectedTreeNode = treeNode.nodeData;
          }
        }
        state.showAddNewForm = null;
        break;
      }

      case 'SET_EXPANDED':
        Tree.nodeFromPath(action.payload.treeNodePath, state.treeNodes).isExpanded =
          action.payload.isExpanded;
        break;

      // UI operations

      case 'SHOW_ADD_NEW_FORM':
        forEachNode(state.treeNodes, (node) => (node.isSelected = false));
        state.selectedTreeNode = null;
        state.showAddNewForm = action.payload.addNewForm;
        break;
    }

    // Update node counts for any change to parameters (all non-UI actions)
    switch (action.type) {
      case 'SET_SELECTED':
      case 'SET_EXPANDED':
      case 'SHOW_ADD_NEW_FORM':
        break;

      default:
        state.counts = getNodeCountsFromParams(
          state.nodeClasses,
          state.enclaveClasses,
          state.enclaves
        );
    }
  }
);

// -- Hook

const initialState: RangeConfigGenerationParametersState = {
  nodeClasses: {},
  enclaveClasses: {
    global: {
      nodes: [],
    },
  },
  enclaves: [{ enclaveClassName: 'global', enclaveQuantity: 1 }],
  counts: {
    type: {
      client: 0,
      server: 0,
    },
    platform: {
      android: 0,
      linux: 0,
    },
    genesis: {
      true: 0,
      false: 0,
    },
    bridge: {
      true: 0,
      false: 0,
    },
  },
  treeNodes: [
    {
      className: 'tl-node-classes',
      id: 'tl-node-classes',
      icon: 'folder-open',
      label: 'Node Classes',
      nodeData: { type: 'nodeClasses' },
      hasCaret: true,
      isExpanded: true,
      isSelected: false,
      childNodes: [],
    },
    {
      className: 'tl-enclave-classes',
      id: 'tl-enclave-classes',
      icon: 'folder-open',
      label: 'Enclave Classes',
      nodeData: { type: 'enclaveClasses' },
      hasCaret: true,
      isExpanded: true,
      isSelected: false,
      childNodes: [],
    },
    {
      className: 'tl-enclaves',
      id: 'tl-enclaves',
      icon: 'folder-open',
      label: 'Enclaves',
      nodeData: { type: 'enclaves' },
      hasCaret: true,
      isExpanded: true,
      isSelected: false,
      childNodes: [],
    },
  ],
  selectedTreeNode: null,
  showAddNewForm: null,
};

initialState.treeNodes[1].childNodes = createEnclaveClassTree(
  initialState.enclaveClasses,
  initialState.nodeClasses
);
initialState.treeNodes[2].childNodes = createEnclaveTree(initialState.enclaves);

export const useRangeConfigGenerationParameters = (): UseRangeConfigGenerationParametersReturn => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const addNodeClass = useCallback(
    (name: string, nodeClass: NodeClassParams) =>
      dispatch({ type: 'ADD_NODE_CLASS', payload: { name, nodeClass } }),
    [dispatch]
  );
  const updateNodeClass = useCallback(
    (name: string, nodeClass: NodeClassParams, oldName?: string) =>
      dispatch({ type: 'UPDATE_NODE_CLASS', payload: { name, nodeClass, oldName } }),
    [dispatch]
  );
  const removeNodeClass = useCallback(
    (name: string) => dispatch({ type: 'REMOVE_NODE_CLASS', payload: { name } }),
    [dispatch]
  );
  const duplicateNodeClass = useCallback(
    (name: string) => dispatch({ type: 'DUPLICATE_NODE_CLASS', payload: { name } }),
    [dispatch]
  );

  const addEnclaveClass = useCallback(
    (name: string, enclaveClass: AddEnclaveClassParams) =>
      dispatch({ type: 'ADD_ENCLAVE_CLASS', payload: { name, enclaveClass } }),
    [dispatch]
  );
  const updateEnclaveClass = useCallback(
    (name: string, enclaveClass: EnclaveClassParams, oldName?: string) =>
      dispatch({ type: 'UPDATE_ENCLAVE_CLASS', payload: { name, enclaveClass, oldName } }),
    [dispatch]
  );
  const removeEnclaveClass = useCallback(
    (name: string) => dispatch({ type: 'REMOVE_ENCLAVE_CLASS', payload: { name } }),
    [dispatch]
  );
  const duplicateEnclaveClass = useCallback(
    (name: string) => dispatch({ type: 'DUPLICATE_ENCLAVE_CLASS', payload: { name } }),
    [dispatch]
  );

  const addEnclave = useCallback(
    (enclave: EnclaveInstanceParams) => dispatch({ type: 'ADD_ENCLAVE', payload: { enclave } }),
    [dispatch]
  );
  const updateEnclave = useCallback(
    (index: number, enclave: EnclaveInstanceParams) =>
      dispatch({ type: 'UPDATE_ENCLAVE', payload: { index, enclave } }),
    [dispatch]
  );
  const removeEnclave = useCallback(
    (index: number) => dispatch({ type: 'REMOVE_ENCLAVE', payload: { index } }),
    [dispatch]
  );
  const duplicateEnclave = useCallback(
    (index: number) => dispatch({ type: 'DUPLICATE_ENCLAVE', payload: { index } }),
    [dispatch]
  );

  const handleNodeClick = useCallback(
    (treeNode: TreeNode, treeNodePath: TreeNodePath) =>
      dispatch({
        type: 'SET_SELECTED',
        payload: { treeNodePath, isSelected: !treeNode.isSelected },
      }),
    [dispatch]
  );
  const handleNodeCollapse = useCallback(
    (treeNode: TreeNode, treeNodePath: TreeNodePath) =>
      dispatch({
        type: 'SET_EXPANDED',
        payload: { treeNodePath, isExpanded: false },
      }),
    [dispatch]
  );
  const handleNodeExpand = useCallback(
    (treeNode: TreeNode, treeNodePath: TreeNodePath) =>
      dispatch({
        type: 'SET_EXPANDED',
        payload: { treeNodePath, isExpanded: true },
      }),
    [dispatch]
  );

  const showAddNewForm = useCallback(
    (addNewForm: AddNewForm) => dispatch({ type: 'SHOW_ADD_NEW_FORM', payload: { addNewForm } }),
    [dispatch]
  );

  return {
    state,
    methods: {
      addNodeClass,
      updateNodeClass,
      removeNodeClass,
      duplicateNodeClass,
      addEnclaveClass,
      updateEnclaveClass,
      removeEnclaveClass,
      duplicateEnclaveClass,
      addEnclave,
      updateEnclave,
      removeEnclave,
      duplicateEnclave,
      handleNodeClick,
      handleNodeCollapse,
      handleNodeExpand,
      showAddNewForm,
    },
  };
};
