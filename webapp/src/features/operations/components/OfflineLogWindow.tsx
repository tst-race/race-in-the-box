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

import { ProgressBar } from '@blueprintjs/core';
import { useCallback } from 'react';

import { usePaginationSearchParams } from '@/hooks/usePaginationSearchParams';

import { useOperationLogs } from '../api/getOperationLogs';

import { LogWindow } from './LogWindow';

type OfflineLogWindowProps = {
  id: number;
};

export const OfflineLogWindow = ({ id }: OfflineLogWindowProps) => {
  const {
    page: offset,
    setPagination,
    size: limit,
  } = usePaginationSearchParams({
    initialPage: 0,
    initialSize: 1000,
    pageKey: 'offset',
    sizeKey: 'limit',
  });

  const setWindow = useCallback(
    ({ limit, offset }: { limit: number; offset: number }) =>
      setPagination({ page: offset, size: limit }),
    [setPagination]
  );

  const query = useOperationLogs({ id, offset, limit });

  return (
    <>
      {query.isFetching && <ProgressBar />}
      {query.data && <LogWindow setWindow={setWindow} {...query.data} />}
    </>
  );
};
