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

import { Button, ButtonGroup, Divider, HTMLSelect, Icon } from '@blueprintjs/core';
import { Tooltip2 } from '@blueprintjs/popover2';
import { useSearchParams } from 'react-router-dom';

import { LogLevel, OperationLogs, OperationOutputLine } from '../../types';
import { toLogLevelInt } from '../../utils/toLogLevelInt';

import styles from './LogWindow.module.css';

const logLevelToClassName: Record<LogLevel, string> = {
  CRITICAL: styles.criticalLevel,
  ERROR: styles.errorLevel,
  WARNING: styles.warningLevel,
  INFO: styles.infoLevel,
  DEBUG: styles.debugLevel,
  TRACE: styles.traceLevel,
  NOTSET: styles.notsetLevel,
};

const logLevelOptions = [
  { label: 'Critical', value: 'CRITICAL' },
  { label: 'Error', value: 'ERROR' },
  { label: 'Warning', value: 'WARNING' },
  { label: 'Info', value: 'INFO' },
  { label: 'Debug', value: 'DEBUG' },
  { label: 'Trace', value: 'TRACE' },
  { label: 'Not-set', value: 'NOTSET' },
];

const TooltipText = ({ line }: { line: OperationOutputLine }) => (
  <div className={styles.tooltip}>
    <span>Source:</span>
    <span>{line.source}</span>
    <span>Level:</span>
    <span>{line.logLevel}</span>
    <span>Time:</span>
    <span>{line.time}</span>
  </div>
);

type LogWindowProps = OperationLogs & {
  isConnected?: boolean;
  isLive?: boolean;
  setWindow: ({ limit, offset }: { limit: number; offset: number }) => void;
};

export const LogWindow = ({
  isConnected = false,
  isLive = false,
  limit,
  lines,
  offset,
  setWindow,
  total,
}: LogWindowProps) => {
  const [searchParams, setSearchParams] = useSearchParams();

  const logLevel = (searchParams.get('level') as LogLevel) || 'INFO';
  const logLevelInt = toLogLevelInt(logLevel);
  const setLogLevel = (level: LogLevel) => {
    searchParams.set('level', level);
    setSearchParams(searchParams);
  };

  return (
    <div className={styles.logWindow}>
      <ButtonGroup className={styles.toolbar}>
        {isLive && (
          <>
            <div className={styles.liveStatus}>
              LIVE
              <Icon icon="full-circle" intent={isConnected ? 'success' : 'danger'} />
            </div>
            <Divider />
          </>
        )}
        <HTMLSelect
          onChange={(event) => setLogLevel(event.currentTarget.value as LogLevel)}
          options={logLevelOptions}
          value={logLevel}
        />
        <div className={styles.pagination}>
          <Button
            disabled={offset - limit / 2 <= 0}
            icon="double-chevron-left"
            onClick={() => setWindow({ limit, offset: 0 })}
            text="first"
          />
          <Button
            disabled={offset <= 0}
            icon="chevron-left"
            onClick={() => setWindow({ limit, offset: Math.max(0, offset - limit / 2) })}
            text="prev"
          />
          <Button
            disabled={offset + limit >= total}
            onClick={() => setWindow({ limit, offset: offset + limit / 2 })}
            rightIcon="chevron-right"
            text="next"
          />
          <Button
            disabled={offset + limit + limit / 2 >= total}
            onClick={() => setWindow({ limit, offset: Math.floor(total / limit) * limit })}
            rightIcon="double-chevron-right"
            text="last"
          />
        </div>
      </ButtonGroup>

      {lines.map((line, index) =>
        toLogLevelInt(line.logLevel) < logLevelInt ? null : (
          <div key={`${index + offset}`} className={styles.logLine}>
            <Tooltip2
              className={styles.lineNumber}
              content={<TooltipText line={line} />}
              openOnTargetFocus={false}
            >
              <span>{`${index + offset + 1}`}</span>
            </Tooltip2>
            <span className={logLevelToClassName[line.logLevel]}>
              {line.text.split('\n').map((subLine, subIndex) => (
                <div key={`${index + offset}.${subIndex}`}>{subLine}</div>
              ))}
            </span>
          </div>
        )
      )}
    </div>
  );
};
