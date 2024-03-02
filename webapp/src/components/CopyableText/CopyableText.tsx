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

import { Button } from '@blueprintjs/core';
import clsx from 'clsx';
import copy from 'copy-to-clipboard';

import { getToaster } from '@/lib/toaster';

import styles from './CopyableText.module.css';

export type CopyableTextProps = {
  border?: boolean;
  code?: boolean;
  displayText?: string;
  text?: string;
};

export const CopyableText = ({
  border = false,
  code = false,
  displayText,
  text,
}: CopyableTextProps) => {
  const handleClick = () => {
    if (text) {
      if (copy(text)) {
        getToaster().show({
          intent: 'none',
          message: 'Text copied to clipboard',
        });
      }
    }
  };

  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions
    <div
      className={clsx(styles.copyable, {
        [styles.border]: border,
        [styles.code]: code,
      })}
      onClick={handleClick}
    >
      <span>{displayText || text}</span>
      <Button icon="clipboard" />
    </div>
  );
};
