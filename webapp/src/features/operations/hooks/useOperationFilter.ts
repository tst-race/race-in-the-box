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

import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';

import { OperationFilter } from '../types';

export type UseOperationFilterResult = {
  filters: OperationFilter | undefined;
  setFilters: (filter: OperationFilter | null) => void;
  target: string | undefined;
};

export const useOperationFilter = (): UseOperationFilterResult => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [filters, target] = useMemo(() => {
    const targetName = searchParams.get('targetName');
    const targetType = searchParams.get('targetType');

    if (targetName && targetType) {
      const filters: OperationFilter = {
        targetName,
        targetType,
      };
      return [filters, `${targetType}:${targetName}`];
    }

    return [undefined, undefined];
  }, [searchParams]);

  const setFilters = useCallback(
    (filters: OperationFilter | null) => {
      searchParams.delete('targetName');
      searchParams.delete('targetType');

      if (filters) {
        searchParams.set('targetName', filters.targetName);
        searchParams.set('targetType', filters.targetType);
      }

      setSearchParams(searchParams, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  return {
    filters,
    setFilters,
    target,
  };
};
