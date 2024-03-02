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

import { Button, ButtonGroup } from '@blueprintjs/core';

export type MessageListPaginationProps = {
  hasPrev: boolean;
  hasNext: boolean;
  setPageForward: () => void;
  setPageBackward: () => void;
};

export const MessageListPagination = ({
  hasPrev,
  hasNext,
  setPageForward,
  setPageBackward,
}: MessageListPaginationProps) => {
  return (
    <ButtonGroup>
      <Button
        disabled={!hasPrev}
        icon="chevron-left"
        onClick={() => setPageBackward()}
        text="Prev"
      />
      <Button
        disabled={!hasNext}
        rightIcon="chevron-right"
        onClick={() => setPageForward()}
        text="Next"
      />
    </ButtonGroup>
  );
};
