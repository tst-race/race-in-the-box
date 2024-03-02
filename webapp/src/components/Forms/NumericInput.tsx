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

import {
  FormGroup,
  Intent,
  NumericInput as BpNumericInput,
  NumericInputProps as BpNumericInputProps,
} from '@blueprintjs/core';
import { FieldPath, UseControllerProps, useController } from 'react-hook-form';

export type NumericInputProps<Inputs> = {
  control: UseControllerProps<Inputs>['control'];
  id: FieldPath<Inputs>;
  inputProps?: Omit<BpNumericInputProps, 'min' | 'max'>;
  max?: number;
  min?: number;
  label?: string;
  required?: boolean | string;
};

export const NumericInput = <Inputs,>({
  control,
  id,
  inputProps = {},
  label,
  max,
  min,
  required = true,
}: NumericInputProps<Inputs>) => {
  const {
    field: { ref, onChange, value, ...fieldProps },
    fieldState: { error },
  } = useController({ control, name: id });

  const numberValue = (() => {
    if (typeof value == 'number') {
      return value as number;
    }
    if (typeof value == 'string') {
      return value as string;
    }
    return undefined;
  })();

  return (
    <FormGroup
      label={label}
      labelFor={String(id)}
      labelInfo={required && '(required)'}
      intent={error && Intent.DANGER}
      subLabel={error?.message}
    >
      <BpNumericInput
        id={String(id)}
        inputRef={ref}
        intent={error && Intent.DANGER}
        {...inputProps}
        {...fieldProps}
        max={max}
        min={min}
        onValueChange={(num) => onChange(num)}
        value={numberValue}
      />
    </FormGroup>
  );
};
