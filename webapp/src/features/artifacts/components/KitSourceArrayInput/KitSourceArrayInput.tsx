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

import { Button, FormGroup } from '@blueprintjs/core';
import {
  ArrayPath,
  FieldArrayWithId,
  FieldErrors,
  Path,
  UseFormRegister,
  get,
  UseFormSetValue,
} from 'react-hook-form';

import { KitSourceArrayEntryInput } from './KitSourceArrayEntryInput';
import styles from './KitSourceArrayInput.module.css';

type KitSourceArrayEntry = {
  value: string;
};

type KitSourceArrayInputProps<Inputs> = {
  onAppend: (entry: KitSourceArrayEntry) => void;
  errors: FieldErrors<Inputs>;
  fields: FieldArrayWithId<Inputs, ArrayPath<Inputs>, 'id'>[];
  label: string;
  name: ArrayPath<Inputs>;
  onRemove: (index: number) => void;
  preferredRaceVersion?: string;
  register: UseFormRegister<Inputs>;
  required?: boolean;
  setValue: UseFormSetValue<Inputs>;
};

export const KitSourceArrayInput = <Inputs,>({
  errors,
  fields,
  label,
  name,
  onAppend,
  onRemove,
  register,
  required = false,
  setValue,
}: KitSourceArrayInputProps<Inputs>) => {
  return (
    <>
      <FormGroup
        className={styles.labelButton}
        inline
        label={label}
        labelInfo={required ? '(required)' : undefined}
      >
        <Button icon="add" id={`${name}-add`} onClick={() => onAppend({ value: '' })} text="Add" />
      </FormGroup>

      {fields.map((field, index) => (
        <KitSourceArrayEntryInput
          key={field.id}
          error={get(errors, `${name}.${index}.value`)}
          id={`${name}.${index}.value` as Path<Inputs>}
          onRemove={fields.length > 1 ? () => onRemove(index) : undefined}
          register={register}
          setValue={setValue}
        />
      ))}
    </>
  );
};
