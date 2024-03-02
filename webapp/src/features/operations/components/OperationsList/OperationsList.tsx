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

import { Divider, NonIdealState } from '@blueprintjs/core';

import { Pagination } from '@/components/Pagination';
import { usePaginationSearchParams } from '@/hooks/usePaginationSearchParams';

import { useQueuedOperations } from '../../api/getQueuedOperations';
import { useOperationFilter } from '../../hooks/useOperationFilter';
import { useOperationTimeDisplayType } from '../../hooks/useOperationTimeDisplayType';
import {
  OperationListItem,
  OperationListItemHeader,
  OperationListItemSkeleton,
} from '../OperationListItem';
import { OperationsListToolbar } from '../OperationsListToolbar';

import styles from './OperationsList.module.css';

export const OperationsList = () => {
  const { filters, setFilters, target } = useOperationFilter();
  const { page, setPage, size } = usePaginationSearchParams();
  const query = useQueuedOperations({ page, size, target });

  const { displayType, setDisplayType } = useOperationTimeDisplayType();

  return (
    <>
      <OperationsListToolbar
        displayType={displayType}
        filters={filters}
        setDisplayType={setDisplayType}
        setFilters={setFilters}
      />
      <Divider />
      <OperationListItemHeader displayType={displayType} />
      {query.isFetching && <OperationListItemSkeleton />}
      {query.isSuccess && query.data.operations.length == 0 && (
        <NonIdealState title="No operations in the queue" />
      )}
      {!query.isFetching &&
        query.data &&
        query.data.operations.map((operation) => (
          <OperationListItem key={operation.id} displayType={displayType} operation={operation} />
        ))}
      <div className={styles.pagination}>
        <Pagination page={page} setPage={setPage} size={size} total={query.data?.total || 0} />
      </div>
    </>
  );
};
