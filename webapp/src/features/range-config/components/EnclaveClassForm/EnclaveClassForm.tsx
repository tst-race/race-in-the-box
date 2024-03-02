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

import { Button, Callout, FormGroup, Intent } from '@blueprintjs/core';
import { yupResolver } from '@hookform/resolvers/yup';
import { useEffect, useMemo } from 'react';
import { SubmitHandler, useFieldArray, useForm } from 'react-hook-form';
import * as yup from 'yup';

import { ActionButtons } from '@/components/ActionButtons';
import { TextInput } from '@/components/Forms';
import { EnclaveClassTemplateSelect, useFetchNodeClassTemplates } from '@/features/templates';

import styles from './EnclaveClassForm.module.css';
import { NodeInstance } from './NodeInstance';
import { Inputs, emptyEnclaveClass, emptyNodeInstance } from './types';

const validatePortOverlap = ({
  nodeQuantity = 0,
  portMapping = [],
}: {
  nodeQuantity?: number;
  portMapping?: {
    startExternalPort?: number;
  }[];
}) => {
  const portRanges: [number, number][] = [];
  for (const { startExternalPort = 0 } of portMapping) {
    const stopExternalPort = startExternalPort + nodeQuantity - 1;
    for (const [startPort, stopPort] of portRanges) {
      if (stopExternalPort >= startPort && startExternalPort <= stopPort) {
        return false;
      }
    }
    portRanges.push([startExternalPort, stopExternalPort]);
  }
  return true;
};

const createSchema = (existingNames: string[]) =>
  yup.object({
    name: yup.string().required('').notOneOf(existingNames, 'name must be unique'),
    nodes: yup
      .array(
        yup
          .object({
            nodeClassName: yup.string().required(''),
            nodeQuantity: yup.number().min(1, ''),
            portMapping: yup.array(
              yup.object({
                startExternalPort: yup.number(),
                internalPort: yup.number(),
              })
            ),
          })
          .test('port-overlap', 'port ranges are overlapping', validatePortOverlap)
      )
      .min(1),
  });

export type EnclaveClassFormProps = {
  defaultValues?: Inputs;
  enclaveClasses: string[];
  isModify?: boolean;
  isTemplate?: boolean;
  nodeClasses: string[];
  onSubmit: SubmitHandler<Inputs>;
};

export const EnclaveClassForm = ({
  defaultValues = emptyEnclaveClass,
  enclaveClasses,
  isModify = false,
  isTemplate = false,
  nodeClasses,
  onSubmit,
}: EnclaveClassFormProps) => {
  const schema = useMemo(
    () => createSchema(enclaveClasses.filter((name) => name != defaultValues.name)),
    [defaultValues.name, enclaveClasses]
  );
  const {
    control,
    formState: { errors, isDirty },
    handleSubmit,
    register,
    reset,
    setValue,
    watch,
  } = useForm<Inputs>({ defaultValues, resolver: yupResolver(schema) });

  const {
    fields: nodeFields,
    append: nodeAppend,
    remove: nodeRemove,
  } = useFieldArray<Inputs>({ control, name: 'nodes' });

  useEffect(() => {
    reset(defaultValues);
  }, [defaultValues, reset]);

  const handleReset = () => reset();
  const handleClick = handleSubmit(onSubmit);

  const watchName = watch('name');
  const handleApplyTemplate = ({ name, ...template }: Omit<Inputs, 'nodeClasses'>) =>
    reset({ name: watchName || name, nodeClasses: {}, ...template }, { keepDefaultValues: true });

  // Auto-fetch and save off node classes that need to be auto-imported along
  // with this enclave class
  const watchNodes = watch('nodes');
  useFetchNodeClassTemplates({
    names: watchNodes
      .map((node) => node.nodeClassName)
      .filter((name) => name && !nodeClasses.includes(name)),
    config: {
      onSuccess: ({ name, ...nodeClass }) => {
        setValue(`nodeClasses.${name}`, nodeClass);
      },
    },
  });

  return (
    <>
      {(!isModify || !isTemplate) && (
        <TextInput
          error={errors.name}
          id="name"
          label={`Enclave Class${isTemplate ? ' Template' : ''} Name`}
          register={register}
        />
      )}

      {!isModify && !isTemplate && <EnclaveClassTemplateSelect onApply={handleApplyTemplate} />}

      <FormGroup className={styles.hbox} inline label="Nodes" labelInfo="(required)">
        <Button icon="add" onClick={() => nodeAppend(emptyNodeInstance)} text="Add nodes" />
      </FormGroup>

      {errors.nodes?.message && (
        <Callout className={styles.errorCallout} intent={Intent.DANGER}>
          {errors.nodes.message}
        </Callout>
      )}

      {nodeFields.map((field, index) => (
        <NodeInstance
          key={field.id}
          control={control}
          errors={errors}
          index={index}
          nodeClasses={nodeClasses}
          onRemove={nodeFields.length > 1 ? nodeRemove : undefined}
          register={register}
        />
      ))}

      <ActionButtons>
        <Button onClick={handleReset} style={{ marginRight: '10px' }} text="Reset" />
        <Button
          onClick={handleClick}
          icon={isModify ? 'floppy-disk' : 'add'}
          intent={!isModify || isDirty ? Intent.SUCCESS : Intent.NONE}
          text={
            isModify
              ? `Update enclave class${isTemplate ? ' template' : ''}`
              : `Add enclave class${isTemplate ? ' template' : ''}`
          }
        />
      </ActionButtons>
    </>
  );
};
