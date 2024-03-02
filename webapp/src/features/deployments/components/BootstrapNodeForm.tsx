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

import { Button, Spinner } from '@blueprintjs/core';
import { SubmitHandler, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

import { ActionButtons } from '@/components/ActionButtons';
import { SelectInput, Switch, TextInput } from '@/components/Forms';
import { randomString } from '@/utils/randomString';

import { useBootstrapNode } from '../api/bootstrapNode';
import { useDeploymentNodesByStatus } from '../api/getDeploymentNodesByStatus';
import { BootstrapNodeRequest, DeploymentMode } from '../types';

type Inputs = BootstrapNodeRequest;

const defaultValues: Partial<Inputs> = {
  introducer: '',
  passphrase: randomString(20),
  architecture: 'x86_64',
  timeout: 600,
};

type BootstrapNodeFormProps = {
  force?: boolean;
  mode: DeploymentMode;
  name: string;
  target?: string;
};

export const BootstrapNodeForm = ({
  force = false,
  mode,
  name,
  target = '',
}: BootstrapNodeFormProps) => {
  const bootstrap = useBootstrapNode();
  const navigate = useNavigate();

  const targets = useDeploymentNodesByStatus({
    app: 'NOT_INSTALLED',
    mode,
    name,
  });
  const introducers = useDeploymentNodesByStatus({
    app: 'RUNNING',
    mode,
    name,
  });

  const form = useForm<Inputs>({ defaultValues: { ...defaultValues, force, target } });

  const onSubmit: SubmitHandler<Inputs> = (data) =>
    bootstrap.mutate(
      { data, mode, name },
      {
        onSuccess: (result) => navigate(`/operations/${result.id}`),
      }
    );

  const handleGeneratePassphrase = () => form.setValue('passphrase', randomString(20));

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {targets.data ? (
        <SelectInput
          error={form.formState.errors.target}
          id="target"
          inputProps={{ options: targets.data.nodes }}
          label="Node to be bootstrapped"
          register={form.register}
        />
      ) : (
        <Spinner />
      )}
      <SelectInput
        error={form.formState.errors.architecture}
        id="architecture"
        inputProps={{ options: ['x86_64', 'arm64-v8a'] }}
        label="Architecture of node to be bootstrapped"
        register={form.register}
      />
      {introducers.data ? (
        <SelectInput
          error={form.formState.errors.introducer}
          id="introducer"
          inputProps={{ options: introducers.data.nodes }}
          label="Node to perform introduction"
          register={form.register}
        />
      ) : (
        <Spinner />
      )}
      <TextInput
        error={form.formState.errors.passphrase}
        id="passphrase"
        label="Secret passphrase"
        register={form.register}
      >
        <Button icon="refresh" onClick={handleGeneratePassphrase} />
      </TextInput>
      <Switch alignIndicator="right" label="Force bootstrap?" {...form.register('force')} />
      <ActionButtons>
        <Button onClick={() => navigate(-1)}>Cancel</Button>
        <Button intent="primary" type="submit">
          Bootstrap
        </Button>
      </ActionButtons>
    </form>
  );
};
