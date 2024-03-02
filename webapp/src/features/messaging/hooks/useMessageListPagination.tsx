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

import { produce } from 'immer';
import { useCallback, useReducer } from 'react';

import { SortValsTypes } from '../types';

// -- Types

export type MessageListPaginationState = {
  pageSortVals: SortValsTypes[];
  pageNum: number;
  hasPrev: boolean;
  hasNext: boolean;
};

const initialState: MessageListPaginationState = {
  pageSortVals: [null],
  pageNum: 0,
  hasPrev: false,
  hasNext: false,
};

export type MessageListPaginationAction =
  | { type: 'ADD_PAGE'; payload: { pageSortVals: SortValsTypes[] } }
  | { type: 'PAGE_FORWARD' }
  | { type: 'PAGE_BACKWARD' }
  | { type: 'RESET' };

// -- Functions

const reducer = produce(
  (state: MessageListPaginationState, action: MessageListPaginationAction) => {
    switch (action.type) {
      case 'ADD_PAGE':
        //check for duplicates, assuming there is only one list in the payload
        if (state.pageSortVals.indexOf(action.payload.pageSortVals[0]) < 0) {
          state.pageSortVals = [...state.pageSortVals, ...action.payload.pageSortVals];
          state.hasNext = true;
        }
        break;

      case 'PAGE_FORWARD':
        if (state.pageNum < state.pageSortVals.length) {
          state.pageNum = state.pageNum + 1;
        }
        state.hasPrev = true;
        if (state.pageNum >= state.pageSortVals.length - 1) {
          state.hasNext = false;
        }
        break;

      case 'PAGE_BACKWARD':
        if (state.pageNum >= 1) {
          state.pageNum = state.pageNum - 1;
          state.hasPrev = state.pageNum > 0;
          state.hasNext = true;
        }
        break;

      case 'RESET':
        state.pageSortVals = [null];
        state.pageNum = 0;
        state.hasPrev = false;
        state.hasNext = false;
        break;
    }
  }
);

// -- Hook

export const useMessageListPagination = () => {
  const [state, dispatch] = useReducer(reducer, initialState);

  const addPage = useCallback(
    (pageSortVals: SortValsTypes[]) => dispatch({ type: 'ADD_PAGE', payload: { pageSortVals } }),
    [dispatch]
  );
  const setPageForward = useCallback(() => dispatch({ type: 'PAGE_FORWARD' }), [dispatch]);
  const setPageBackward = useCallback(() => dispatch({ type: 'PAGE_BACKWARD' }), [dispatch]);
  const reset = useCallback(() => dispatch({ type: 'RESET' }), [dispatch]);

  return {
    ...state,
    addPage,
    setPageForward,
    setPageBackward,
    reset,
  };
};
