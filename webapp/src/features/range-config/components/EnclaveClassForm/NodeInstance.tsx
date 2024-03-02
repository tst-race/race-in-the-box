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

import { Button, Callout, Card, Elevation, FormGroup, Intent } from '@blueprintjs/core';
import {
  Control,
  FieldErrors,
  UseFormRegister,
  get,
  useFieldArray,
  useWatch,
} from 'react-hook-form';

import { NumericInput, SelectInput } from '@/components/Forms';
import { ENABLE_PORT_MAPPING } from '@/config';

import { useNodeClassImportRequired } from '../../hooks/useNodeClassImportRequired';

import styles from './EnclaveClassForm.module.css';
import { Inputs, emptyPortMapping } from './types';

type NodeClassEntryProps = {
  control: Control<Inputs>;
  errors: FieldErrors<Inputs>;
  index: number;
  nodeClasses: string[];
  onRemove?: (index: number) => void;
  register: UseFormRegister<Inputs>;
};

export const NodeInstance = ({
  control,
  errors,
  index,
  nodeClasses,
  onRemove,
  register,
}: NodeClassEntryProps) => {
  const {
    fields: portFields,
    append: portAppend,
    remove: portRemove,
  } = useFieldArray<Inputs>({
    control,
    name: `nodes.${index}.portMapping`,
  });

  const watchName = useWatch<Inputs>({ control, name: `nodes.${index}.nodeClassName` }) as string;
  const [nodeClassImportRequired, adjustedNodeClasses] = useNodeClassImportRequired(
    watchName,
    nodeClasses
  );

  return (
    <Card className={styles.nodeCard} elevation={Elevation.TWO}>
      <div className={styles.nodeClassQuantity}>
        <SelectInput
          error={get(errors, `nodes.${index}.nodeClassName`)}
          id={`nodes.${index}.nodeClassName`}
          inputProps={{ options: adjustedNodeClasses }}
          label="Node Class"
          register={register}
        />
        <NumericInput
          control={control}
          id={`nodes.${index}.nodeQuantity`}
          max={10000}
          min={1}
          label="Node Quantity"
        />
      </div>

      {ENABLE_PORT_MAPPING && (
        <>
          <FormGroup className={styles.hbox} inline label="Port Mappings">
            <Button
              icon="add"
              onClick={() => portAppend(emptyPortMapping)}
              text="Add Port Mapping"
            />
          </FormGroup>

          {portFields.length > 0 && (
            <div className={styles.portMappings}>
              <FormGroup label="Start External Port" labelInfo="(required)" />
              <FormGroup label="Internal Port" labelInfo="(required)" />
            </div>
          )}
          {portFields.map((field, portIndex) => (
            <div key={field.id} className={styles.portMappings}>
              <NumericInput
                control={control}
                id={`nodes.${index}.portMapping.${portIndex}.startExternalPort`}
                max={65535}
                min={1}
              />
              <NumericInput
                control={control}
                id={`nodes.${index}.portMapping.${portIndex}.internalPort`}
                max={65535}
                min={1}
              />
              <Button icon="delete" onClick={() => portRemove(portIndex)} />
            </div>
          ))}
        </>
      )}

      {nodeClassImportRequired && (
        <Callout className={styles.errorCallout} intent={Intent.WARNING}>
          node class will be auto-imported
        </Callout>
      )}

      {errors.nodes?.[index]?.message && (
        <Callout className={styles.errorCallout} intent={Intent.DANGER}>
          {errors.nodes?.[index]?.message}
        </Callout>
      )}

      <Button
        disabled={!onRemove}
        icon="delete"
        onClick={onRemove ? () => onRemove(index) : undefined}
        text="Remove nodes"
      />
    </Card>
  );
};
