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

import { FormGroup, HTMLSelect, HTMLSelectProps, Intent } from '@blueprintjs/core';
import clsx from 'clsx';
import { FieldError, FieldPath, Merge, UseFormRegister } from 'react-hook-form';

import styles from './SelectInput.module.css';

export type SelectInputProps<Inputs, TFieldName extends FieldPath<Inputs> = FieldPath<Inputs>> = {
  error?: FieldError | Merge<FieldError, any>;
  id: TFieldName;
  inputProps?: HTMLSelectProps;
  label?: string;
  register: UseFormRegister<Inputs>;
  required?: boolean | string;
};

export const SelectInput = <Inputs, TFieldName extends FieldPath<Inputs> = FieldPath<Inputs>>({
  error,
  id,
  inputProps = {},
  label,
  register,
  required = true,
}: SelectInputProps<Inputs, TFieldName>) => {
  const { ref, ...fieldProps } = register(id, {
    required: required && (typeof required == 'boolean' ? 'select an option' : required),
  });
  return (
    <FormGroup
      label={label}
      labelFor={String(id)}
      labelInfo={required && '(required)'}
      intent={error && Intent.DANGER}
      subLabel={error?.message}
    >
      <HTMLSelect
        className={clsx({ [styles.error]: error != undefined })}
        id={String(id)}
        elementRef={ref}
        {...inputProps}
        {...fieldProps}
      />
    </FormGroup>
  );
};
