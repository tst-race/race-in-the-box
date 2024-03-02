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

import { Alignment, Button, Intent } from '@blueprintjs/core';
import { yupResolver } from '@hookform/resolvers/yup';
import { useEffect, useMemo } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';
import * as yup from 'yup';

import { ActionButtons } from '@/components/ActionButtons';
import { SelectInput, Switch, TextInput } from '@/components/Forms';
import { NodeClassTemplateSelect } from '@/features/templates';

import { NodeClassParams } from '../../types';

import styles from './NodeClassForm.module.css';

export type Inputs = NodeClassParams & {
  name: string;
};

const emptyNodeClass: Inputs = {
  name: '',
  type: 'client',
  nat: false,
  genesis: true,
  gpu: false,
  bridge: false,
  platform: 'linux',
  architecture: 'x86_64',
  environment: 'any',
};

const createSchema = (existingNames: string[]) =>
  yup.object({
    name: yup.string().required('').notOneOf(existingNames, 'name must be unique'),
    platform: yup.string().when('type', {
      is: (val: string) => val == 'client',
      then: (schema) => schema.oneOf(['linux', 'android']),
      otherwise: (schema) => schema.oneOf(['linux']),
    }),
    genesis: yup.bool().when('type', {
      is: (val: string) => val == 'client',
      then: (schema) => schema.oneOf([true, false]),
      otherwise: (schema) => schema.oneOf([true]),
    }),
    bridge: yup.bool().when('platform', {
      is: (val: string) => val == 'android',
      then: (schema) => schema.oneOf([true, false]),
      otherwise: (schema) => schema.oneOf([false]),
    }),
    gpu: yup.bool().when('platform', {
      is: (val: string) => val == 'linux',
      then: (schema) => schema.oneOf([true, false]),
      otherwise: (schema) => schema.oneOf([false]),
    }),
    environment: yup.string().required(''),
  });

const nodeTypeSelectProps = {
  options: ['client', 'server'],
};

const platformSelectProps = {
  options: ['linux', 'android'],
};

const archSelectProps = {
  options: ['x86_64', 'arm64-v8a'],
};
const bridgeArchSelectProps = {
  options: ['auto'],
};

export type NodeClassFormProps = {
  defaultValues?: Inputs;
  isModify?: boolean;
  isTemplate?: boolean;
  nodeClasses: string[];
  onSubmit: SubmitHandler<Inputs>;
};

export const NodeClassForm = ({
  defaultValues = emptyNodeClass,
  isModify = false,
  isTemplate = false,
  nodeClasses,
  onSubmit,
}: NodeClassFormProps) => {
  const schema = useMemo(
    () => createSchema(nodeClasses.filter((name) => name != defaultValues.name)),
    [defaultValues.name, nodeClasses]
  );
  const {
    formState: { errors, isDirty },
    handleSubmit,
    register,
    reset,
    setValue,
    watch,
  } = useForm<Inputs>({ defaultValues, resolver: yupResolver(schema) });

  useEffect(() => {
    reset(defaultValues);
  }, [defaultValues, reset]);

  const handleReset = () => reset();
  const handleClick = handleSubmit(onSubmit);

  // Update available options depending on selected type & platform
  const watchName = watch('name');
  const watchType = watch('type');
  const watchPlatform = watch('platform');
  const watchBridge = watch('bridge');
  useEffect(() => {
    const subscription = watch((data, { name }) => {
      if (name == 'type') {
        if (data[name] == 'server') {
          setValue('platform', 'linux');
          setValue('genesis', true);
        }
      }
      if (name == 'platform') {
        if (data[name] == 'linux') {
          setValue('bridge', false);
        } else {
          setValue('gpu', false);
        }
      }
      if (name == 'bridge') {
        if (data[name]) {
          setValue('architecture', 'auto');
        } else if (data['architecture'] == 'auto') {
          setValue('architecture', 'x86_64');
        }
      }
    });
    return () => subscription.unsubscribe();
  }, [setValue, watch]);

  const handleApplyTemplate = ({ name, ...template }: Inputs) =>
    reset({ name: watchName || name, ...template }, { keepDefaultValues: true });

  return (
    <>
      {(!isModify || !isTemplate) && (
        <TextInput
          error={errors.name}
          id="name"
          label={`Node Class${isTemplate ? ' Template' : ''} Name`}
          register={register}
        />
      )}

      {!isModify && !isTemplate && <NodeClassTemplateSelect onApply={handleApplyTemplate} />}

      <div className={styles.selectInputs}>
        <SelectInput
          error={errors.type}
          id="type"
          inputProps={nodeTypeSelectProps}
          label="Node Type"
          register={register}
        />
        <SelectInput
          error={errors.platform}
          id="platform"
          inputProps={{
            disabled: watchType == 'server',
            ...platformSelectProps,
          }}
          label="Platform"
          register={register}
        />
        <SelectInput
          error={errors.architecture}
          id="architecture"
          inputProps={{
            disabled: watchBridge,
            ...(watchBridge ? bridgeArchSelectProps : archSelectProps),
          }}
          label="Architecture"
          register={register}
        />
      </div>
      <Switch
        alignIndicator={Alignment.RIGHT}
        disabled={watchType == 'server'}
        innerLabel="no"
        innerLabelChecked="yes"
        label="Genesis?"
        {...register('genesis')}
      />
      <Switch
        alignIndicator={Alignment.RIGHT}
        disabled={watchPlatform == 'linux'}
        innerLabel="managed"
        innerLabelChecked="bridged"
        label="Bridged?"
        {...register('bridge')}
      />
      <Switch
        alignIndicator={Alignment.RIGHT}
        disabled={watchPlatform == 'android'}
        innerLabel="disabled"
        innerLabelChecked="enabled"
        label="GPU enabled?"
        {...register('gpu')}
      />
      <Switch
        alignIndicator={Alignment.RIGHT}
        innerLabel="disabled"
        innerLabelChecked="enabled"
        label="NAT enabled?"
        {...register('nat')}
      />
      <TextInput
        error={errors.environment}
        id="environment"
        label="Environment Tag"
        register={register}
      />
      <ActionButtons>
        <Button onClick={handleReset} style={{ marginRight: '10px' }} text="Reset" />
        <Button
          onClick={handleClick}
          icon={isModify ? 'floppy-disk' : 'add'}
          intent={!isModify || isDirty ? Intent.SUCCESS : Intent.NONE}
          text={
            isModify
              ? `Update node class${isTemplate ? ' template' : ''}`
              : `Add node class${isTemplate ? ' template' : ''}`
          }
        />
      </ActionButtons>
    </>
  );
};
