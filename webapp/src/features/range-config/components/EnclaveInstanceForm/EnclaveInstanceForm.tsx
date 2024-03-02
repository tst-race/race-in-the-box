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

import { Button, FormGroup, HTMLSelect, Intent } from '@blueprintjs/core';
import { yupResolver } from '@hookform/resolvers/yup';
import { useEffect } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import * as yup from 'yup';

import { ActionButtons } from '@/components/ActionButtons';
import { NumericInput, SelectInput } from '@/components/Forms';
import { ENABLE_TEMPLATES } from '@/config';

import { EnclaveInstanceParams } from '../../types';

import styles from './EnclaveInstanceForm.module.css';

type Inputs = EnclaveInstanceParams;

const emptyEnclaveInstance: Readonly<Inputs> = {
  enclaveClassName: '',
  enclaveQuantity: 1,
};

const schema = yup.object({
  enclaveClassName: yup.string().required(''),
  enclaveQuantity: yup.number().min(1, ''),
});

export type EnclaveInstanceFormProps = {
  defaultValues?: Inputs;
  enclaveClasses: string[];
  isModify: boolean;
  onSubmit: SubmitHandler<Inputs>;
};

export const EnclaveInstanceForm = ({
  defaultValues = emptyEnclaveInstance,
  enclaveClasses,
  isModify,
  onSubmit,
}: EnclaveInstanceFormProps) => {
  const {
    control,
    formState: { errors, isDirty },
    handleSubmit,
    register,
    reset,
  } = useForm<Inputs>({ defaultValues, resolver: yupResolver(schema) });

  useEffect(() => {
    reset(defaultValues);
  }, [defaultValues, reset]);

  const handleReset = () => reset();
  const handleClick = handleSubmit(onSubmit);

  return (
    <>
      {ENABLE_TEMPLATES && (
        <FormGroup inline label="Enclave Template" labelFor="enclaveInstanceTemplate">
          <HTMLSelect disabled options={['Select...']} />
        </FormGroup>
      )}

      <div className={styles.enclaveClassQuantity}>
        <SelectInput
          error={errors.enclaveClassName}
          id="enclaveClassName"
          inputProps={{ options: enclaveClasses }}
          label="Enclave Class"
          register={register}
        />
        <NumericInput
          control={control}
          id="enclaveQuantity"
          max={10000}
          min={1}
          label="Enclave Quantity"
        />
      </div>

      <ActionButtons>
        <Button onClick={handleReset} style={{ marginRight: '10px' }} text="Reset" />
        <Button
          onClick={handleClick}
          icon={isModify ? 'floppy-disk' : 'add'}
          intent={!isModify || isDirty ? Intent.SUCCESS : Intent.NONE}
          text={isModify ? 'Update enclave' : 'Add enclave'}
        />
      </ActionButtons>
    </>
  );
};
