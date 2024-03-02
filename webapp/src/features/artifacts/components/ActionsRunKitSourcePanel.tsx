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

import { useForm } from 'react-hook-form';

import { TextInput } from '@/components/Forms';

import { KitSourcePanelProps } from '../types';

import { KitSourcePanel } from './KitSourcePanel/KitSourcePanel';

type Inputs = {
  org: string;
  repo: string;
  run: string;
  asset: string;
};

const defaultValues: Inputs = {
  org: '',
  repo: '',
  run: '',
  asset: '',
};

export const ActionsRunKitSourcePanel = ({ onReset, onSelect }: KitSourcePanelProps) => {
  const form = useForm<Inputs>({ defaultValues });
  const onSubmit = form.handleSubmit((values: Inputs) => {
    let source = `run=${values.run}`;
    if (values.org) {
      source = `${source},org=${values.org}`;
    }
    if (values.repo) {
      source = `${source},repo=${values.repo}`;
    }
    if (values.asset) {
      source = `${source},asset=${values.asset}`;
    }
    onSelect(source);
  });

  return (
    <KitSourcePanel onReset={onReset} onSubmit={onSubmit}>
      <TextInput
        error={form.formState.errors.org}
        id="org"
        label="GitHub org/owner of the repo (leave empty to use default)"
        register={form.register}
        required={false}
      />
      <TextInput
        error={form.formState.errors.repo}
        id="repo"
        label="GitHub repository (leave empty to use default)"
        register={form.register}
        required={false}
      />
      <TextInput
        error={form.formState.errors.run}
        id="run"
        label="GitHub Actions workflow run ID"
        register={form.register}
      />
      <TextInput
        error={form.formState.errors.asset}
        id="asset"
        label="Artifact name (leave empty to use repo name as asset name)"
        register={form.register}
        required={false}
      />
    </KitSourcePanel>
  );
};
