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

import { Switch as BpSwitch, SwitchProps as BpSwitchProps } from '@blueprintjs/core';
import { forwardRef } from 'react';
import { UseFormRegisterReturn } from 'react-hook-form';

type SwitchProps = BpSwitchProps & Pick<UseFormRegisterReturn, 'ref'>;

export const Switch = forwardRef<HTMLInputElement, SwitchProps>((props, ref) => (
  <BpSwitch inputRef={ref != null ? ref : undefined} {...props} />
));
Switch.displayName = 'Switch';
