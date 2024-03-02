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

import { ButtonProps, Icon } from '@blueprintjs/core';
import clsx from 'clsx';

import { StateColor } from '../../types';
import { getColorPalette } from '../../utils/getColorPalette';

import styles from './StateTransition.module.css';

type StateTransitionProps = {
  color?: StateColor;
  disabled?: boolean;
  height?: number;
  inverted?: boolean;
  name: string;
  onClick?: ButtonProps['onClick'];
  reverse?: boolean;
  width?: number;
  xPos?: number;
  yPos?: number;
};

export const StateTransition = ({
  color = 'black',
  disabled = false,
  height = 50,
  inverted = false,
  name,
  onClick,
  reverse = false,
  width = 100,
  xPos = 0,
  yPos = 0,
}: StateTransitionProps) => {
  const palette = getColorPalette(color, disabled);
  return (
    <div
      className={clsx(styles.stateTransition, {
        [styles.inverted]: inverted,
        [styles.reverse]: reverse,
      })}
      style={{ borderColor: `${palette.border}b3`, height, left: xPos, top: yPos, width }}
    >
      <button
        className={clsx({
          [styles.interactive]: !disabled && onClick != undefined,
        })}
        disabled={disabled || onClick == undefined}
        onClick={onClick}
        style={{ borderColor: palette.border, color: palette.border }}
      >
        {reverse && <Icon icon="arrow-left" size={14} />}
        {name}
        {!reverse && <Icon icon="arrow-right" size={14} />}
      </button>
    </div>
  );
};
