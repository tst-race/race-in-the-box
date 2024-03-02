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

import { MessageTrace } from '../../types';
import { MessageDuration } from '../MessageDuration';
import { MessageItemStatus } from '../MessageItemStatus';
import { MessageStartTime } from '../MessageStartTime';
import { MessageStopTime } from '../MessageStopTime';
import { MessageTestId } from '../MessageTestId';
import { MessageTraceId } from '../MessageTraceId';

export type MessageListItemProps = {
  message: MessageTrace;
};

export const MessageListItem = ({ message }: MessageListItemProps) => (
  <>
    <tr key={message.send_span ? message.send_span.trace_id : message.receive_span.trace_id}>
      <MessageItemStatus state={message.status} />
      <td>{message.send_span ? message.send_span.source_persona : 'NA'}</td>
      <td>{message.receive_span ? message.receive_span.source_persona : 'NA'}</td>
      <MessageTestId sendSpan={message.send_span} receiveSpan={message.receive_span} />
      <MessageTraceId sendSpan={message.send_span} receiveSpan={message.receive_span} />
      <MessageStartTime startedTime={message.send_span ? message.send_span.start_time : null} />
      <MessageStopTime
        stoppedTime={message.receive_span ? message.receive_span.start_time : null}
      />
      {message.receive_span && message.send_span ? (
        <MessageDuration
          startedTime={message.send_span.start_time}
          stoppedTime={message.receive_span.start_time}
        />
      ) : (
        <td> {'00:00:00'} </td>
      )}
    </tr>
  </>
);
