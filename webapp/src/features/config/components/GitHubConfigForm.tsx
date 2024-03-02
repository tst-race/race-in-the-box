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

import React from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';

import { FormButtons, SecretInput, TextInput } from '@/components/Forms';

import { useGitHubConfig } from '../api/getGitHubConfig';
import { useUpdateGitHubConfig } from '../api/updateGitHubConfig';
import { GitHubConfig } from '../types';

type Inputs = GitHubConfig;

const DEFAULTS: Inputs = {
  access_token: '',
  username: '',
  default_org: '',
  default_race_images_org: '',
  default_race_images_repo: '',
  default_race_images_tag: '',
  default_race_core_org: '',
  default_race_core_repo: '',
  default_race_core_source: '',
};

export const GitHubConfigForm = () => {
  const { isLoading, mutate } = useUpdateGitHubConfig();
  const {
    formState: { errors },
    handleSubmit,
    register,
    reset,
  } = useForm<Inputs>({ defaultValues: DEFAULTS });
  const onSubmit: SubmitHandler<Inputs> = (data) => mutate({ data });

  const { data } = useGitHubConfig();
  React.useEffect(() => {
    if (data) {
      reset(data);
    }
  }, [data, reset]);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <SecretInput
        error={errors.access_token}
        helperText="Needed to use kits from private GitHub repositories"
        id="access_token"
        label="GitHub Personal Access Token"
        register={register}
        required={false}
      />

      <TextInput
        error={errors.username}
        helperText="Needed to use private Docker images from GitHub"
        id="username"
        label="GitHub Account Username"
        register={register}
        required={false}
      />

      <TextInput
        error={errors.default_org}
        id="default_org"
        label="Default GitHub organization/owner"
        register={register}
        required={false}
      />

      <TextInput
        error={errors.default_race_images_org}
        helperText="If blank, the default GitHub org will be used"
        id="default_race_images_org"
        label="Default GitHub organization/owner for RACE images"
        register={register}
        required={false}
      />

      <TextInput
        error={errors.default_race_images_repo}
        helperText="If blank, 'race-images' will be used"
        id="default_race_images_repo"
        inputProps={{ placeholder: 'race-images' }}
        label="Default GitHub repository for RACE images"
        register={register}
        required={false}
      />

      <TextInput
        error={errors.default_race_images_tag}
        helperText="If blank, 'latest' will be used"
        id="default_race_images_tag"
        inputProps={{ placeholder: 'latest' }}
        label="Default RACE images tag"
        register={register}
        required={false}
      />

      <TextInput
        error={errors.default_race_core_org}
        helperText="If blank, the default GitHub org will be used"
        id="default_race_core_org"
        label="Default GitHub organization/owner for RACE core"
        register={register}
        required={false}
      />

      <TextInput
        error={errors.default_race_core_repo}
        helperText="If blank, 'race-core' will be used"
        id="default_race_core_repo"
        inputProps={{ placeholder: 'race-core' }}
        label="Default GitHub repository for RACE core"
        register={register}
        required={false}
      />

      <TextInput
        error={errors.default_race_core_source}
        id="default_race_core_source"
        label="Default source for RACE core"
        register={register}
        required={false}
      />

      <FormButtons isLoading={isLoading} reset={reset} submitText="Save" />
    </form>
  );
};
