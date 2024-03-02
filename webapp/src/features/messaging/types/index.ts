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

import { DeploymentMode } from '@/features/deployments';

export * from './sends';

//opaque type that front end doesn't need to care about
//thus [] of any instead of a more specific type
export type SortValsTypes = [] | null;

export type MessageListBase = {
  mode: DeploymentMode;
  name: string;
  search_after_vals: SortValsTypes[];
};

export type MessageListFilter = {
  recipient?: string | null;
  sender?: string | null;
  test_id?: string | null;
  trace_id?: string | null;
  date_from?: string | null;
  date_to?: string | null;
  reverse_sort?: boolean | null;
  size?: number | null;
};

export type MessageListRequest = MessageListBase & MessageListFilter;

export type MessageSpan = {
  trace_id: string;
  span_id: string;
  start_time: number;
  source_persona: string;
  messageSize: number;
  messageHash: string;
  messageTestId: string;
  messageFrom: string;
  messageTo: string;
};

export type MessageStatus = 'ERROR' | 'SENT' | 'RECEIVED' | 'CORRUPTED';

export type MessageTrace = {
  status: MessageStatus;
  send_span: MessageSpan;
  receive_span: MessageSpan;
};

export type MessageListResponse = {
  messages: MessageTrace[];
  has_more_pages: boolean;
} & MessageListBase;
