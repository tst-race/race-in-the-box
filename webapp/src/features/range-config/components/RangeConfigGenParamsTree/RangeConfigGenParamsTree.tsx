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

import { Tree } from '@blueprintjs/core';

import {
  RangeConfigGenerationParametersMethods,
  RangeConfigGenerationParametersState,
} from '../../hooks/useRangeConfigGenerationParameters';

import styles from './RangeConfigGenParamsTree.module.css';

type RangeConfigGenParamsTreeProps = {
  methods: RangeConfigGenerationParametersMethods;
  treeNodes: RangeConfigGenerationParametersState['treeNodes'];
};

export const RangeConfigGenParamsTree = ({ methods, treeNodes }: RangeConfigGenParamsTreeProps) => (
  <div className={styles.tree}>
    <Tree
      contents={treeNodes}
      onNodeClick={methods.handleNodeClick}
      onNodeCollapse={methods.handleNodeCollapse}
      onNodeExpand={methods.handleNodeExpand}
    />
  </div>
);
