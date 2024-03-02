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

import {
  Button,
  Callout,
  Card,
  FormGroup,
  H4,
  Intent,
  Spinner,
  SpinnerSize,
  Tab,
  Tabs,
} from '@blueprintjs/core';
import { yupResolver } from '@hookform/resolvers/yup';
import { useEffect } from 'react';
import { SubmitHandler, useFieldArray, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import * as yup from 'yup';

import { ActionButtons } from '@/components/ActionButtons';
import { SelectInput, Switch, TextInput } from '@/components/Forms';
import { TextArrayInput } from '@/components/Forms/TextArrayInput';
import { KitSourceArrayInput, KitSourceInput } from '@/features/artifacts';
import { useGitHubConfig } from '@/features/config';
import {
  EnclaveClassParams,
  EnclaveInstanceParams,
  generateRangeConfig,
  NodeClassParams,
  RangeConfigGenParams,
  useRangeConfigGenerationParameters,
} from '@/features/range-config';

import { useCreateLocalDeployment } from '../../api/createLocalDeployment';
import { LocalDeploymentCreateRequest } from '../../types';

import styles from './CreateLocalDeploymentForm.module.css';

type Inputs = Omit<
  LocalDeploymentCreateRequest,
  'range_config' | 'comms_channels' | 'comms_kits' | 'artifact_manager_kits'
> & {
  comms_channels: {
    value: string;
  }[];
  comms_kits: {
    value: string;
  }[];
  artifact_manager_kits: {
    value: string;
  }[];
  nodeClasses: Record<string, NodeClassParams>;
  enclaveClasses: Record<string, EnclaveClassParams>;
  enclaves: EnclaveInstanceParams[];
};

const defaultValues: Inputs = {
  name: '',
  race_core: '',
  network_manager_kit: '',
  comms_channels: [{ value: '' }],
  comms_kits: [{ value: '' }],
  artifact_manager_kits: [
    // Order is important here
    { value: 'core=plugin-artifact-manager-twosix-cpp-local' },
    { value: 'core=plugin-artifact-manager-twosix-cpp' },
  ],
  android_app: 'core=raceclient-android',
  linux_app: 'core=racetestapp-linux',
  node_daemon: 'core=race-node-daemon',
  android_client_image: 'race-runtime-android-x86_64',
  linux_client_image: 'race-runtime-linux',
  linux_server_image: 'race-runtime-linux',
  nodeClasses: {},
  enclaveClasses: {},
  enclaves: [],
  fetch_plugins_on_start: false,
  no_config_gen: false,
  disable_config_encryption: false,
  enable_gpu: false,
  cache: 'auto',
  race_log_level: 'info',
};

export const schema = yup.object({
  name: yup.string().required(''),
  race_core: yup.string().required(''),
  network_manager_kit: yup.string().required(''),
  comms_channels: yup
    .array(
      yup.object({
        value: yup.string().required(''),
      })
    )
    .min(1),
  comms_kits: yup
    .array(
      yup.object({
        value: yup.string().required(''),
      })
    )
    .min(1),
  artifact_manager_kits: yup
    .array(
      yup.object({
        value: yup.string().required(''),
      })
    )
    .min(1),
  android_app: yup.string().required(''),
  linux_app: yup.string().required(''),
  node_daemon: yup.string().required(''),
  android_client_image: yup.string().required(''),
  linux_client_image: yup.string().required(''),
  linux_server_image: yup.string().required(''),
  enclaves: yup.array().min(1, 'Must have at least one enclave'),
});

const cacheInputProps = {
  options: [
    { label: 'Auto, based on source type', value: 'auto' },
    { label: 'Always re-use cached kit', value: 'always' },
    { label: 'Always re-download kit', value: 'never' },
  ],
};

const logLevelProps = {
  options: ['debug', 'info', 'warning', 'error'],
};

export const CreateLocalDeploymentForm = () => {
  const create = useCreateLocalDeployment();
  const navigate = useNavigate();

  const {
    control,
    formState: { dirtyFields, errors },
    handleSubmit,
    register,
    setValue,
  } = useForm<Inputs>({ defaultValues, resolver: yupResolver(schema) });
  const comms_channels = useFieldArray({ control, name: 'comms_channels' });
  const comms_kits = useFieldArray({ control, name: 'comms_kits' });
  const amp_kits = useFieldArray({ control, name: 'artifact_manager_kits' });

  useGitHubConfig({
    config: {
      onSuccess: (ghConfig) => {
        if (ghConfig.default_race_core_source && !dirtyFields.race_core) {
          setValue('race_core', ghConfig.default_race_core_source);
        }
      },
    },
  });

  const { state: rangeConfigParamsState, methods: rangeConfigParamsMethods } =
    useRangeConfigGenerationParameters();

  useEffect(
    () => setValue('nodeClasses', rangeConfigParamsState.nodeClasses),
    [rangeConfigParamsState.nodeClasses, setValue]
  );
  useEffect(
    () => setValue('enclaveClasses', rangeConfigParamsState.enclaveClasses),
    [rangeConfigParamsState.enclaveClasses, setValue]
  );
  useEffect(
    () => setValue('enclaves', rangeConfigParamsState.enclaves),
    [rangeConfigParamsState.enclaves, setValue]
  );

  const onSubmit: SubmitHandler<Inputs> = ({
    enclaves,
    enclaveClasses,
    nodeClasses,
    ...inputs
  }: Inputs) => {
    const data: LocalDeploymentCreateRequest = {
      ...inputs,
      comms_channels: inputs.comms_channels.map((channel) => channel.value),
      comms_kits: inputs.comms_kits.map((kit) => kit.value),
      artifact_manager_kits: inputs.artifact_manager_kits.map((kit) => kit.value),
      range_config: generateRangeConfig(nodeClasses, enclaveClasses, enclaves),
    };
    create.mutate(
      { data },
      {
        onSuccess: (result) => navigate(`/operations/${result.id}`),
      }
    );
  };

  const BasicFields = () => (
    <>
      <TextInput error={errors.name} id="name" label="Deployment Name" register={register} />
      <KitSourceInput
        allowCore={false}
        error={errors.race_core}
        id="race_core"
        label="RACE Core"
        register={register}
        setValue={setValue}
      />
      <KitSourceInput
        error={errors.network_manager_kit}
        id="network_manager_kit"
        label="Network Manager Kit"
        register={register}
        setValue={setValue}
      />
      <TextArrayInput
        errors={errors}
        fields={comms_channels.fields}
        label="Comms Channels"
        name="comms_channels"
        onAppend={comms_channels.append}
        onRemove={comms_channels.remove}
        required
        register={register}
      />
      <KitSourceArrayInput
        errors={errors}
        fields={comms_kits.fields}
        label="Comms Kits"
        name="comms_kits"
        onAppend={comms_kits.append}
        onRemove={comms_kits.remove}
        register={register}
        required
        setValue={setValue}
      />

      <FormGroup label="Nodes &amp; Enclaves" labelInfo="(required)">
        {errors.enclaves && <Callout intent={Intent.DANGER}>{errors.enclaves.message}</Callout>}
        <Card className={styles.nodeInput} id="nodes_and_enclaves">
          <RangeConfigGenParams methods={rangeConfigParamsMethods} state={rangeConfigParamsState} />
        </Card>
      </FormGroup>
    </>
  );

  const AdvancedFields = () => (
    <>
      <H4>Configuration</H4>
      <Switch
        alignIndicator="right"
        label="Skip default config generation after creating deployment?"
        {...register('no_config_gen')}
      />
      <Switch
        alignIndicator="right"
        label="Fetch plugins on app startup using artifact managers?"
        {...register('fetch_plugins_on_start')}
      />
      <Switch
        alignIndicator="right"
        label="Disable encryption of configs on RACE nodes?"
        {...register('disable_config_encryption')}
      />
      <Switch
        alignIndicator="right"
        label="Enable pass-through GPU support to all RACE node containers?"
        {...register('enable_gpu')}
      />
      <SelectInput
        error={errors.race_log_level}
        id="race_log_level"
        inputProps={logLevelProps}
        label="RACE application log level"
        register={register}
      />
      <H4>Apps and Plugins</H4>
      <SelectInput
        error={errors.cache}
        id="cache"
        inputProps={cacheInputProps}
        label="Downloaded kit caching behavior"
        register={register}
      />
      <KitSourceInput
        error={errors.android_app}
        id="android_app"
        label="RACE Android App"
        register={register}
        setValue={setValue}
      />
      <KitSourceInput
        error={errors.linux_app}
        id="linux_app"
        label="RACE Linux App"
        register={register}
        setValue={setValue}
      />
      <KitSourceInput
        error={errors.node_daemon}
        id="node_daemon"
        label="RACE Node Daemon"
        register={register}
        setValue={setValue}
      />
      <KitSourceArrayInput
        errors={errors}
        fields={amp_kits.fields}
        label="Artifact Manager Kits"
        name="artifact_manager_kits"
        onAppend={amp_kits.append}
        onRemove={amp_kits.remove}
        register={register}
        required
        setValue={setValue}
      />
      <H4>Docker Images</H4>
      <TextInput
        error={errors.android_client_image}
        id="android_client_image"
        label="Docker Image for Android Client Nodes"
        register={register}
      />
      <TextInput
        error={errors.linux_client_image}
        id="linux_client_image"
        label="Docker Image for Linux Client Nodes"
        register={register}
      />
      <TextInput
        error={errors.linux_server_image}
        id="linux_server_image"
        label="Docker Image for Linux Server Nodes"
        register={register}
      />
    </>
  );

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Tabs id="local-deployment-create">
        <Tab id="basic" title="Basic" panel={<BasicFields />} />
        <Tab id="advanced" title="Advanced" panel={<AdvancedFields />} />
      </Tabs>

      <ActionButtons>
        <Button onClick={() => navigate('..')} text="Cancel" />
        <Button
          disabled={create.isLoading}
          id="create_deployment"
          intent={Intent.PRIMARY}
          type="submit"
        >
          {create.isLoading ? <Spinner size={SpinnerSize.SMALL} /> : 'Create Deployment'}
        </Button>
      </ActionButtons>
    </form>
  );
};
