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

import { Divider, HTMLTable, NonIdealState } from '@blueprintjs/core';

import { DeploymentMode } from '@/features/deployments';

import { useMessageList } from '../../api/getMessageList';
import { useMessageListFilter } from '../../hooks/useMessageListFilter';
import { useMessageListPagination } from '../../hooks/useMessageListPagination';
import { MessageListFilter } from '../../types';
import {
  MessageListItem,
  MessageListItemHeader,
  MessageListItemSkeleton,
} from '../MessageListItem';
import { MessageListPagination } from '../MessageListPagination';
import { MessageListToolbar } from '../MessageListToolbar';

export type MessageListProps = {
  mode: DeploymentMode;
  name: string;
};

export const MessageList = ({ mode, name }: MessageListProps) => {
  const { filters, setFilters } = useMessageListFilter();
  const page = useMessageListPagination();

  const search_after_vals = page.pageSortVals[page.pageNum] || [];

  const query = useMessageList({
    mode,
    name,
    search_after_vals,
    ...filters,
    config: {
      onSuccess(data) {
        page.addPage(data.search_after_vals);
      },
    },
  });

  const handleSetFilters = (filter: MessageListFilter | null) => {
    setFilters(filter);
    page.reset();
  };

  return (
    <>
      <MessageListToolbar filters={filters} setFilters={handleSetFilters} mode={mode} name={name} />
      <Divider />
      <HTMLTable striped={true}>
        {!query.isLoading && <MessageListItemHeader />}
        {query.isLoading && <MessageListItemSkeleton />}
        {query.isSuccess && query.data.messages.length == 0 && (
          <NonIdealState title="No messages were found" />
        )}
        <tbody>
          {!query.isFetching &&
            query.data &&
            query.data.messages.map((message) => (
              <MessageListItem
                message={message}
                key={message.send_span ? message.send_span.trace_id : message.receive_span.trace_id}
              />
            ))}
        </tbody>
      </HTMLTable>
      {!query.isFetching && query.data && (
        <MessageListPagination
          setPageForward={page.setPageForward}
          setPageBackward={page.setPageBackward}
          hasPrev={page.hasPrev}
          hasNext={page.hasNext && query.data.has_more_pages}
        />
      )}
    </>
  );
};
