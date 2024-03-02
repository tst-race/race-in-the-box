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

import { Button, FormGroup, HTMLSelectProps } from '@blueprintjs/core';
import { Fragment } from 'react';
import {
  ArrayPath,
  FieldArrayWithId,
  FieldErrors,
  UseFormRegister,
  get,
  Path,
} from 'react-hook-form';

import { SelectInput, TextInput } from '@/components/Forms';

import styles from './CustomArgsInput.module.css';

export type CustomArgs = {
  pluginId: string;
  args: string;
};

type CustomArgsInputProps<Inputs> = {
  onAppend: (args: CustomArgs) => void;
  errors: FieldErrors<Inputs>;
  fields: FieldArrayWithId<Inputs, ArrayPath<Inputs>, 'id'>[];
  label: string;
  name: ArrayPath<Inputs>;
  onRemove: (index: number) => void;
  options: HTMLSelectProps['options'];
  register: UseFormRegister<Inputs>;
  type: 'plugin' | 'channel';
};

export const CustomArgsInput = <Inputs,>({
  errors,
  fields,
  label,
  name,
  onAppend,
  onRemove,
  options,
  register,
  type,
}: CustomArgsInputProps<Inputs>) => (
  <>
    <FormGroup className={styles.labelButton} inline label={label}>
      <Button
        icon="add"
        onClick={() => onAppend({ pluginId: '', args: '' })}
        text={`Add ${type} args`}
      />
    </FormGroup>

    <div className={styles.inputs}>
      {fields.map((field, index) => (
        <Fragment key={field.id}>
          <SelectInput
            error={get(errors, `${name}.${index}.pluginId`)}
            id={`${name}.${index}.pluginId` as Path<Inputs>}
            inputProps={{ fill: true, options }}
            register={register}
            required={true}
          />
          <TextInput
            error={get(errors, `${name}.${index}.args`)}
            id={`${name}.${index}.args` as Path<Inputs>}
            inputProps={{ placeholder: '--arg=value' }}
            register={register}
          />
          <Button icon="delete" onClick={() => onRemove(index)} />
        </Fragment>
      ))}
    </div>
  </>
);
