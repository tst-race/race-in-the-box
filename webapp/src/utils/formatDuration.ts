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

import { intervalToDuration } from 'date-fns';

import { toDate } from './toDate';

const zeroPad = (num: number) => String(num).padStart(2, '0');

export const formatDuration = (
  startTime: number | string | Date,
  endTime: number | string | Date
): string => {
  const duration = intervalToDuration({
    start: toDate(startTime),
    end: toDate(endTime),
  });
  return [
    zeroPad(duration.hours || 0),
    zeroPad(duration.minutes || 0),
    zeroPad(duration.seconds || 0),
  ].join(':');
};
