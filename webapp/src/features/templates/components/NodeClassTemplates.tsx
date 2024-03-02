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

import { NonIdealState } from '@blueprintjs/core';

import { NavCard } from '@/components/NavCard';

import { useNodeClassTemplates } from '../api/getNodeClassTemplates';

export const NodeClassTemplates = () => {
  const query = useNodeClassTemplates();

  return (
    <>
      {query.isLoading && <NavCard text="" to="" skeleton />}
      {query.isSuccess && query.data.nodeClasses.length == 0 && (
        <NonIdealState title="No node class templates exist" />
      )}
      {query.data &&
        query.data.nodeClasses.map((name) => <NavCard key={name} text={name} to={name} />)}
    </>
  );
};
