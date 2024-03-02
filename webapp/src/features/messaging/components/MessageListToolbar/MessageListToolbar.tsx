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

import { MessageListProps } from '../MessageList/MessageList';
import { MessageListFilterInput, MessageListFilterInputProps } from '../MessageListFilterInput';

import styles from './MessageListToolbar.module.css';

type MessageListToolbarProps = MessageListFilterInputProps & MessageListProps;

export const MessageListToolbar = ({
  filters,
  setFilters,
  mode,
  name,
}: MessageListToolbarProps) => (
  <div className={styles.toolbar}>
    <MessageListFilterInput filters={filters} setFilters={setFilters} mode={mode} name={name} />
  </div>
);
