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

import { MessageListFilter } from '../types';

export type UseMessageListFilterResult = {
  filters: MessageListFilter | undefined;
  setFilters: (filter: MessageListFilter | null) => void;
};

export const useMessageListFilter = (): UseMessageListFilterResult => {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters = useMemo(() => {
    const size = Number(searchParams.get('size') || 50);
    const recipient = searchParams.get('recipient');
    const sender = searchParams.get('sender');
    const test_id = searchParams.get('test_id');
    const trace_id = searchParams.get('trace_id');
    const date_from = searchParams.get('date_from');
    const date_to = searchParams.get('date_to');
    //store the boolean version instead of the string version
    const reverse_sort = searchParams.get('reverse_sort') === 'true';

    const filters: MessageListFilter = {
      size,
      recipient,
      sender,
      test_id,
      trace_id,
      date_from,
      date_to,
      reverse_sort,
    };

    return filters;
  }, [searchParams]);

  const setFilters = useCallback(
    (filters: MessageListFilter | null) => {
      searchParams.delete('size');
      searchParams.delete('recipient');
      searchParams.delete('sender');
      searchParams.delete('test_id');
      searchParams.delete('trace_id');
      searchParams.delete('date_from');
      searchParams.delete('date_to');
      searchParams.delete('reverse_sort');

      if (filters) {
        for (const [key, value] of Object.entries(filters)) {
          //check if null or undefined, then call toString if no problem
          //check for boolean version and convert back to string
          if (value === true || value === false) {
            searchParams.set(key, value.toString());
          } else if (value) {
            if (typeof value === 'number') {
              searchParams.set(key, value.toString());
            } else {
              searchParams.set(key, value);
            }
          }
        }
      }

      setSearchParams(searchParams, { replace: true });
    },
    [searchParams, setSearchParams]
  );

  return {
    filters,
    setFilters,
  };
};
