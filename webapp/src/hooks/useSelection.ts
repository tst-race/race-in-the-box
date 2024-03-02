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

import { Dispatch, SetStateAction, useCallback, useState } from 'react';

export type UseSelectionResult<T> = {
  addToSelection: (value: T) => void;
  removeFromSelection: (value: T) => void;
  selection: T[];
  setSelection: Dispatch<SetStateAction<T[]>>;
  toggleSelection: (value: T) => void;
};

export const useSelection = <T>(initial: T[] = []): UseSelectionResult<T> => {
  const [selection, setSelection] = useState<T[]>(initial);

  const addToSelection = useCallback((value: T) => setSelection((prev) => [...prev, value]), []);
  const removeFromSelection = useCallback(
    (value: T) => setSelection((prev) => prev.filter((v) => v != value)),
    []
  );
  const toggleSelection = useCallback(
    (value: T) =>
      setSelection((prev) => {
        if (prev.includes(value)) {
          return prev.filter((v) => v != value);
        } else {
          return [...prev, value];
        }
      }),
    []
  );

  return {
    addToSelection,
    removeFromSelection,
    selection,
    setSelection,
    toggleSelection,
  };
};
