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

import { Divider } from '@blueprintjs/core';
import { useMemo } from 'react';

import { SplitPane } from '@/components/SplitPane';

import {
  RangeConfigGenerationParametersMethods,
  RangeConfigGenerationParametersState,
} from '../../hooks/useRangeConfigGenerationParameters';
import { EnclaveClassForm } from '../EnclaveClassForm';
import { EnclaveInstanceForm } from '../EnclaveInstanceForm';
import { NodeClassForm } from '../NodeClassForm';
import { NodeCountSummary } from '../NodeCountSummary';
import { RangeConfigGenParamsToolbar } from '../RangeConfigGenParamsToolbar';
import { RangeConfigGenParamsTree } from '../RangeConfigGenParamsTree';

export type RangeConfigGenParamsProps = {
  methods: RangeConfigGenerationParametersMethods;
  state: RangeConfigGenerationParametersState;
};

export const RangeConfigGenParams = ({ methods, state }: RangeConfigGenParamsProps) => {
  const rightElement = useMemo(() => {
    if (state.showAddNewForm == 'nodeClass') {
      return (
        <NodeClassForm
          isModify={false}
          nodeClasses={Object.keys(state.nodeClasses)}
          onSubmit={({ name, ...nodeClass }) => methods.addNodeClass(name, nodeClass)}
        />
      );
    }
    if (state.showAddNewForm == 'enclaveClass') {
      return (
        <EnclaveClassForm
          enclaveClasses={Object.keys(state.enclaveClasses)}
          isModify={false}
          nodeClasses={Object.keys(state.nodeClasses)}
          onSubmit={({ name, ...enclaveClass }) => methods.addEnclaveClass(name, enclaveClass)}
        />
      );
    }
    if (state.showAddNewForm == 'enclave') {
      return (
        <EnclaveInstanceForm
          isModify={false}
          enclaveClasses={Object.keys(state.enclaveClasses)}
          onSubmit={methods.addEnclave}
        />
      );
    }
    if (state.selectedTreeNode?.type == 'nodeClass') {
      const oldName = state.selectedTreeNode.name;
      return (
        <NodeClassForm
          defaultValues={{ name: oldName, ...state.nodeClasses[oldName] }}
          isModify
          nodeClasses={Object.keys(state.nodeClasses)}
          onSubmit={({ name, ...enclaveClass }) =>
            methods.updateNodeClass(name, enclaveClass, oldName)
          }
        />
      );
    }
    if (state.selectedTreeNode?.type == 'enclaveClass') {
      const oldName = state.selectedTreeNode.name;
      return (
        <EnclaveClassForm
          defaultValues={{ name: oldName, nodeClasses: {}, ...state.enclaveClasses[oldName] }}
          enclaveClasses={Object.keys(state.enclaveClasses)}
          isModify
          nodeClasses={Object.keys(state.nodeClasses)}
          onSubmit={({ name, ...enclaveClass }) =>
            methods.updateEnclaveClass(name, enclaveClass, oldName)
          }
        />
      );
    }
    if (state.selectedTreeNode?.type == 'enclave') {
      const index = state.selectedTreeNode.index;
      return (
        <EnclaveInstanceForm
          defaultValues={state.enclaves[index]}
          enclaveClasses={Object.keys(state.enclaveClasses)}
          isModify
          onSubmit={(enclave) => methods.updateEnclave(index, enclave)}
        />
      );
    }
    return undefined;
  }, [
    methods,
    state.enclaveClasses,
    state.enclaves,
    state.nodeClasses,
    state.selectedTreeNode,
    state.showAddNewForm,
  ]);

  return (
    <>
      <NodeCountSummary counts={state.counts} />
      <Divider />
      <SplitPane
        leftElement={
          <>
            <RangeConfigGenParamsToolbar
              methods={methods}
              selectedTreeNode={state.selectedTreeNode}
            />
            <Divider />
            <RangeConfigGenParamsTree methods={methods} treeNodes={state.treeNodes} />
          </>
        }
        rightElement={rightElement}
      />
    </>
  );
};
