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

import { useState } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';

import { LiveOperationLogsUpdate, OperationOutputLine } from '../types';

import { LogWindow } from './LogWindow';

type LiveLogWindowProps = {
  id: number;
};

export const LiveLogWindow = ({ id }: LiveLogWindowProps) => {
  const [logLines, setLogLines] = useState<OperationOutputLine[]>([]);

  const { readyState } = useWebSocket(`ws://${window.location.host}/api/operations/${id}/ws`, {
    onMessage: (event) => {
      const update: LiveOperationLogsUpdate = JSON.parse(event.data);
      setLogLines((prev) => prev.concat(update.lines));
    },
    shouldReconnect: () => true,
  });

  return (
    <LogWindow
      isConnected={readyState == ReadyState.OPEN}
      isLive
      limit={Number.POSITIVE_INFINITY}
      lines={logLines}
      offset={0}
      total={0}
      setWindow={() => 0}
    />
  );
};
