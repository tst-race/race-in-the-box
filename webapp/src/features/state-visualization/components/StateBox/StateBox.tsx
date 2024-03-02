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

import clsx from 'clsx';
import { MouseEventHandler } from 'react';

import { StateColor } from '../../types';
import { getColorPalette } from '../../utils/getColorPalette';

import styles from './StateBox.module.css';

export type StateBoxProps = {
  color?: StateColor;
  disabled?: boolean;
  id?: string;
  name: string;
  onClick?: MouseEventHandler<HTMLDivElement>;
  xPos?: number;
  yPos?: number;
};

export const StateBox = ({
  color = 'black',
  disabled = false,
  id,
  name,
  onClick,
  xPos = 0,
  yPos = 0,
}: StateBoxProps) => {
  const palette = getColorPalette(color, disabled);
  return (
    // eslint-disable-next-line jsx-a11y/click-events-have-key-events
    <div
      className={clsx(styles.stateBox, { [styles.interactive]: onClick != undefined })}
      id={id || name}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      style={{
        backgroundColor: palette.background,
        boxShadow: `inset 0 0 0 3px ${palette.border}b3, 0 0 2px ${palette.border}1a`,
        color: palette.text,
        left: xPos,
        top: yPos,
      }}
    >
      {name}
    </div>
  );
};
