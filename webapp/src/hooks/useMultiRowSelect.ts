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

import { MouseEventHandler, useEffect, useMemo, useState } from 'react';

import { UseSelectionResult, useSelection } from './useSelection';

const eventToRowIndex = (event: MouseEvent): number | null => {
  let target = event.target as HTMLTableRowElement;
  while (target.tagName != 'TR') {
    if (target.parentNode == null) {
      return null;
    }
    target = target.parentNode as HTMLTableRowElement;
  }
  return target.rowIndex - 1; // rowIndex is 1-based
};

const createRange = (start: number, end: number): number[] =>
  [...Array(end - start).keys()].map((i) => i + start);

export type UseMultiRowSelectOptions = {
  initial?: number[];
};

type TrProps = {
  onMouseDown: MouseEventHandler<HTMLTableRowElement>;
};

export type UseMultiRowSelectResult = UseSelectionResult<number> & {
  trProps: TrProps;
};

export const useMultiRowSelect = ({
  initial = [],
}: UseMultiRowSelectOptions = {}): UseMultiRowSelectResult => {
  const { setSelection, ...select } = useSelection<number>(initial);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [startIndex, setStartIndex] = useState<number | null>(null);

  const trProps: TrProps = useMemo(
    () => ({
      onMouseDown: (event) => {
        event.preventDefault();
        setStartIndex((prev) => {
          if (prev == null) {
            return eventToRowIndex(event.nativeEvent);
          }
          return prev;
        });
      },
    }),
    [setStartIndex]
  );

  useEffect(() => {
    const handleEndSelection = (event: MouseEvent) => {
      const end = eventToRowIndex(event);
      if (end != null) {
        setStartIndex((start) => {
          if (start != null) {
            const lower = Math.min(start, end);
            const upper = Math.max(start, end);
            setSelection((prev) => {
              if (prev.includes(start)) {
                // De-select all in range
                return prev.filter((index) => index < lower || index > upper);
              } else {
                // Select all in range
                return [...new Set([...prev, ...createRange(lower, upper + 1)])];
              }
            });
          }
          return null;
        });
      } else {
        setStartIndex(null);
      }
    };

    window.addEventListener('mouseup', handleEndSelection);
    return () => window.removeEventListener('mouseup', handleEndSelection);
  }, [setStartIndex, setSelection]);

  return {
    ...select,
    setSelection,
    trProps,
  };
};
