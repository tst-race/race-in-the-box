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

import { Colors } from '@blueprintjs/core';

import { StateColor, StateColorPalette } from '../types';

/* List of colors is [border, background, text] */
const colorPalette: Record<StateColor, string[]> = {
  black: [Colors.BLACK, Colors.WHITE, Colors.BLACK],
  blue: [Colors.BLUE1, Colors.BLUE5, Colors.BLACK],
  cerulean: [Colors.CERULEAN1, Colors.CERULEAN5, Colors.BLACK],
  gold: [Colors.GOLD1, Colors.GOLD5, Colors.BLACK],
  gray: [Colors.GRAY1, Colors.GRAY5, Colors.BLACK],
  green: [Colors.GREEN1, Colors.GREEN5, Colors.BLACK],
  indigo: [Colors.INDIGO1, Colors.INDIGO5, Colors.BLACK],
  lime: [Colors.LIME1, Colors.LIME5, Colors.BLACK],
  red: [Colors.RED1, Colors.RED5, Colors.BLACK],
  rose: [Colors.ROSE1, Colors.ROSE5, Colors.BLACK],
  orange: [Colors.ORANGE1, Colors.ORANGE5, Colors.BLACK],
  sepia: [Colors.SEPIA1, Colors.SEPIA5, Colors.BLACK],
  turquoise: [Colors.TURQUOISE1, Colors.TURQUOISE5, Colors.BLACK],
  violet: [Colors.VIOLET1, Colors.VIOLET5, Colors.BLACK],
};

const disabledPalette = [Colors.GRAY5, Colors.LIGHT_GRAY1, Colors.GRAY3];

export const getColorPalette = (color: StateColor, disabled = false): StateColorPalette => ({
  border: disabled ? disabledPalette[0] : colorPalette[color][0],
  background: disabled ? disabledPalette[1] : colorPalette[color][1],
  text: disabled ? disabledPalette[2] : colorPalette[color][2],
});
