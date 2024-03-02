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

import { Icon, IconProps } from '@blueprintjs/core';

import { MessageStatus } from '../../types';

const stateToIconName: Record<MessageStatus, IconProps['icon']> = {
  SENT: 'exchange',
  RECEIVED: 'tick-circle',
  CORRUPTED: 'cross',
  ERROR: 'error',
};

type MessageItemStatusProps = {
  state: MessageStatus;
};

export const MessageItemStatus = ({ state }: MessageItemStatusProps) => (
  <td>
    <Icon icon={stateToIconName[state]} size={12} />
    {state == 'SENT' && <span> In progress </span>}
    {state == 'RECEIVED' && <span> Complete </span>}
    {(state == 'ERROR' || state == 'CORRUPTED') && <span> Something went wrong! </span>}
  </td>
);
