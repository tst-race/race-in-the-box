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

import { Button } from '@blueprintjs/core';
import { useMemo } from 'react';
import { SubmitHandler, useFieldArray, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

import { ActionButtons } from '@/components/ActionButtons';
import { NumericInput, Switch, TextInput } from '@/components/Forms';

import { useGenerateDeploymentConfig } from '../api/generateDeploymentConfig';
import { useLocalDeploymentInfo } from '../api/getLocalDeploymentInfo';
import { DeploymentMode } from '../types';

import { CustomArgs, CustomArgsInput } from './CustomArgsInput';

type Inputs = {
  network_manager_custom_args: string;
  comms_custom_args: CustomArgs[];
  artifact_manager_custom_args: CustomArgs[];
  force: boolean;
  max_iterations: number;
  skip_config_tar: boolean;
  timeout: number;
};

const defaultValues: Partial<Inputs> = {
  network_manager_custom_args: '',
  comms_custom_args: [],
  artifact_manager_custom_args: [],
  max_iterations: 20,
  timeout: 300,
};

const customArgsArrayToDict = (customArgs: CustomArgs[]): Record<string, string> =>
  customArgs.reduce<Record<string, string>>((argsObj, arg) => {
    argsObj[arg.pluginId] = arg.args;
    return argsObj;
  }, {});

type ConfigGenerationParamsFormProps = {
  force?: boolean;
  mode: DeploymentMode;
  name: string;
  skip_config_tar?: boolean;
};

export const GenerateConfigForm = ({
  force = false,
  mode,
  name,
  skip_config_tar = false,
}: ConfigGenerationParamsFormProps) => {
  const generate = useGenerateDeploymentConfig();
  const navigate = useNavigate();

  const deploymentInfo = useLocalDeploymentInfo({ name });
  const commsChannelIds = useMemo(() => {
    if (deploymentInfo.data) {
      return deploymentInfo.data.config.comms_channels.map((c) => c.name);
    }
    return [];
  }, [deploymentInfo.data]);
  const ampPluginIds = useMemo(() => {
    if (deploymentInfo.data) {
      return deploymentInfo.data.config.artifact_manager_kits.map((p) => p.name);
    }
    return [];
  }, [deploymentInfo.data]);

  const form = useForm<Inputs>({ defaultValues: { ...defaultValues, force, skip_config_tar } });
  const commsCustomArgs = useFieldArray({ control: form.control, name: 'comms_custom_args' });
  const ampCustomArgs = useFieldArray({
    control: form.control,
    name: 'artifact_manager_custom_args',
  });

  const onSubmit: SubmitHandler<Inputs> = ({
    comms_custom_args,
    artifact_manager_custom_args,
    ...inputs
  }) =>
    generate.mutate(
      {
        data: {
          ...inputs,
          comms_custom_args: customArgsArrayToDict(comms_custom_args),
          artifact_manager_custom_args: customArgsArrayToDict(artifact_manager_custom_args),
        },
        mode,
        name,
      },
      {
        onSuccess: (result) => navigate(`/operations/${result.id}`),
      }
    );

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <TextInput
        error={form.formState.errors.network_manager_custom_args}
        id="network_manager_custom_args"
        label="Network Manager Plugin Custom Arguments"
        register={form.register}
        required={false}
      />
      <CustomArgsInput
        errors={form.formState.errors}
        fields={commsCustomArgs.fields}
        label="Comms Channel Custom Arguments"
        name="comms_custom_args"
        onAppend={commsCustomArgs.append}
        onRemove={commsCustomArgs.remove}
        options={commsChannelIds}
        register={form.register}
        type="channel"
      />
      <CustomArgsInput
        errors={form.formState.errors}
        fields={ampCustomArgs.fields}
        label="Artifact Manager Plugin Custom Arguments"
        name="artifact_manager_custom_args"
        onAppend={ampCustomArgs.append}
        onRemove={ampCustomArgs.remove}
        options={ampPluginIds}
        register={form.register}
        type="plugin"
      />
      <Switch alignIndicator="right" label="Force re-generation?" {...form.register('force')} />
      <NumericInput
        control={form.control}
        id="max_iterations"
        label="Max Iterations"
        min={1}
        required={false}
      />
      <Switch
        alignIndicator="right"
        label="Disable creation of config archives?"
        {...form.register('skip_config_tar')}
      />
      <ActionButtons>
        <Button onClick={() => navigate(-1)}>Cancel</Button>
        <Button intent="primary" type="submit">
          Generate Configs
        </Button>
      </ActionButtons>
    </form>
  );
};
