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

import { ControlGroup, FormGroup, InputGroup, InputGroupProps, Intent } from '@blueprintjs/core';
import { ReactNode } from 'react';
import { FieldError, FieldPath, Merge, UseFormRegister } from 'react-hook-form';

export type TextInputProps<Inputs, TFieldName extends FieldPath<Inputs> = FieldPath<Inputs>> = {
  children?: ReactNode;
  error?: FieldError | Merge<FieldError, any>;
  helperText?: string;
  id: TFieldName;
  inputProps?: InputGroupProps;
  label?: string;
  register: UseFormRegister<Inputs>;
  required?: boolean | string;
};

export const TextInput = <Inputs, TFieldName extends FieldPath<Inputs> = FieldPath<Inputs>>({
  children,
  error,
  helperText,
  id,
  inputProps = {},
  label,
  register,
  required = true,
}: TextInputProps<Inputs, TFieldName>) => {
  const { ref, ...fieldProps } = register(id, { required });
  return (
    <FormGroup
      helperText={helperText}
      label={label}
      labelFor={String(id)}
      labelInfo={required && '(required)'}
      intent={error && Intent.DANGER}
      subLabel={error?.message}
    >
      <ControlGroup>
        <InputGroup
          id={String(id)}
          inputRef={ref}
          intent={error && Intent.DANGER}
          fill
          {...inputProps}
          {...fieldProps}
        />
        {children}
      </ControlGroup>
    </FormGroup>
  );
};
