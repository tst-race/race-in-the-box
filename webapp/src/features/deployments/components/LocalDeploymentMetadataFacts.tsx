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

import { H4 } from '@blueprintjs/core';

import { CopyableText } from '@/components/CopyableText';
import { DescriptionList } from '@/components/DescriptionList';

import { useLocalDeploymentConfigSummary } from '../hooks/useLocalDeploymentConfigSummary';

export type LocalDeploymentMetadataFactsProps = {
  name: string;
};

export const LocalDeploymentMetadataFacts = ({ name }: LocalDeploymentMetadataFactsProps) => {
  const { info, isLoading } = useLocalDeploymentConfigSummary({ name });

  return (
    <>
      <H4>Deployment</H4>
      <DescriptionList margin pending={isLoading} striped weight={4}>
        <dt>Creation Time</dt>
        <dd>{info?.metadata.create_date}</dd>
        <dt>Create Command</dt>
        <dd>
          <CopyableText code text={info?.metadata.create_command} />
        </dd>
        <dt>Last Config Generation Time</dt>
        <dd>{info?.metadata.last_config_gen_time}</dd>
        <dt>Last Config Generation Command</dt>
        <dd>
          <CopyableText code text={info?.metadata.last_config_gen_command} />
        </dd>
      </DescriptionList>

      <H4>RiB</H4>
      <DescriptionList margin pending={isLoading} striped weight={4}>
        <dt>Image Tag</dt>
        <dd>{info?.metadata.rib_image.image_tag}</dd>
        <dt>Image Digest</dt>
        <dd>{info?.metadata.rib_image.image_digest}</dd>
        <dt>Image Created</dt>
        <dd>{info?.metadata.rib_image.image_created}</dd>
      </DescriptionList>
    </>
  );
};
