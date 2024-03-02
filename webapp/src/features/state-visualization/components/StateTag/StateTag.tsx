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

import { Tag, TagProps } from '@blueprintjs/core';

import { StateColor } from '../../types';
import { getColorPalette } from '../../utils/getColorPalette';

export type StateTagProps = Omit<TagProps, 'color' | 'intent'> & {
  color?: StateColor;
  disabled?: boolean;
};

export const StateTag = ({ color = 'black', disabled = false, ...props }: StateTagProps) => {
  const palette = getColorPalette(color, disabled);

  return (
    <Tag
      style={{
        backgroundColor: palette.background,
        color: palette.text,
      }}
      {...props}
    />
  );
};
