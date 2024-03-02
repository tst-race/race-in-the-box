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
  path: string;
};

const defaultValues: Inputs = {
  path: '',
};

export const LocalKitSourcePanel = ({ onReset, onSelect }: KitSourcePanelProps) => {
  const form = useForm<Inputs>({ defaultValues });
  const onSubmit = form.handleSubmit((values: Inputs) => onSelect(`local=${values.path}`));

  return (
    <KitSourcePanel onReset={onReset} onSubmit={onSubmit}>
      <TextInput
        error={form.formState.errors.path}
        id="path"
        label="Local Kit Path"
        register={form.register}
      />
    </KitSourcePanel>
  );
};
