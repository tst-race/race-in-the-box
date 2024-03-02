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

import { useSearchParams } from 'react-router-dom';

import { OperationTimeDisplayType } from '../types';

export type UseOperationTimeDisplayTypeResult = {
  displayType: OperationTimeDisplayType;
  setDisplayType: (displayType: OperationTimeDisplayType) => void;
};

export const useOperationTimeDisplayType = (): UseOperationTimeDisplayTypeResult => {
  const [searchParams, setSearchParams] = useSearchParams({ displayType: 'relative' });

  const displayType = searchParams.get('displayType') as OperationTimeDisplayType;
  const setDisplayType = (displayType: OperationTimeDisplayType) => {
    searchParams.set('displayType', displayType);
    setSearchParams(searchParams, { replace: true });
  };

  return {
    displayType,
    setDisplayType,
  };
};
