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

import { Button, ControlGroup, HTMLSelect, InputGroup } from '@blueprintjs/core';
import { useEffect } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';

import { OperationFilter } from '../types';

const targetTypeOptions = [
  { label: 'Local Deployment', value: 'deployment:local' },
  { label: 'AWS Deployment', value: 'deployment:aws' },
];

type Inputs = OperationFilter;

const defaultValues: Inputs = {
  targetName: '',
  targetType: targetTypeOptions[0].value,
};

export type OperationFilterInputProps = {
  filters: OperationFilter | undefined;
  setFilters: (filters: OperationFilter | null) => void;
};

export const OperationFilterInput = ({ filters, setFilters }: OperationFilterInputProps) => {
  const form = useForm<Inputs>({ defaultValues });

  useEffect(() => {
    form.reset(filters || defaultValues);
  }, [filters, form]);

  const onSubmit: SubmitHandler<Inputs> = (inputs) => setFilters(inputs);

  const { ref: targetTypeRef, ...targetTypeProps } = form.register('targetType');
  const { ref: targetNameRef, ...targetNameProps } = form.register('targetName', {
    required: true,
  });

  const handleClear = () => setFilters(null);
  const rightElement = filters ? <Button icon="cross" minimal onClick={handleClear} /> : undefined;

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <ControlGroup>
        <HTMLSelect elementRef={targetTypeRef} options={targetTypeOptions} {...targetTypeProps} />
        <InputGroup
          fill
          inputRef={targetNameRef}
          placeholder="Filter operations..."
          rightElement={rightElement}
          {...targetNameProps}
        />
        <Button icon="search" type="submit" />
      </ControlGroup>
    </form>
  );
};
