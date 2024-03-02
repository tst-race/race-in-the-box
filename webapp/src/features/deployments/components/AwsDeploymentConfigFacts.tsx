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

import { useAwsDeploymentConfigSummary } from '../hooks/useAwsDeploymentConfigSummary';

import { CopyableKitDescription } from './CopyableKitDescription';

export type AwsDeploymentConfigFactsProps = {
  name: string;
};

export const AwsDeploymentConfigFacts = ({ name }: AwsDeploymentConfigFactsProps) => {
  const { info, isLoading, nodeCounts } = useAwsDeploymentConfigSummary({ name });

  return (
    <>
      <H4>Node Counts</H4>
      <DescriptionList margin pending={isLoading} striped weight={4}>
        <dt>Client Node Count</dt>
        <dd>{nodeCounts.type.client}</dd>
        <dt>Server Node Count</dt>
        <dd>{nodeCounts.type.server}</dd>
        <dt>Linux Node Count</dt>
        <dd>{nodeCounts.platform.linux}</dd>
        <dt>Android Node Count</dt>
        <dd>{nodeCounts.platform.android}</dd>
        <dt>Genesis Node Count</dt>
        <dd>{nodeCounts.genesis.true}</dd>
        <dt>Bootstrapped Node Count</dt>
        <dd>{nodeCounts.genesis.false}</dd>
        <dt>Managed (containers) Node Count</dt>
        <dd>{nodeCounts.bridge.false}</dd>
        <dt>Bridged Node Count</dt>
        <dd>{nodeCounts.bridge.true}</dd>
      </DescriptionList>

      <H4>Artifacts</H4>
      <DescriptionList margin pending={isLoading} striped weight={4}>
        <dt>RACE Core</dt>
        <dd>
          <CopyableText code text={info?.config.race_core.raw} />
        </dd>
        <dt>Network Manager Plugin</dt>
        <dd>{info && <CopyableKitDescription kit={info.config.network_manager_kit} />}</dd>
        <dt>Comms Channels</dt>
        <dd>
          {info?.config.comms_channels.map((channel) => (
            <CopyableText
              key={channel.name}
              code
              displayText={`${channel.name} (${channel.kit_name})`}
              text={channel.name}
            />
          ))}
        </dd>
        <dt>Comms Kits</dt>
        <dd>
          {info?.config.comms_kits.map((kit) => (
            <CopyableKitDescription key={kit.name} kit={kit} />
          ))}
        </dd>
        <dt>Artifact Manager Plugins</dt>
        <dd>
          {info?.config.artifact_manager_kits.map((kit) => (
            <CopyableKitDescription key={kit.name} kit={kit} />
          ))}
        </dd>
        <dt>Node Daemon</dt>
        <dd>{info && <CopyableKitDescription kit={info.config.node_daemon} />}</dd>
        <dt>Linux App</dt>
        <dd>{info && <CopyableKitDescription kit={info.config.linux_app} />}</dd>
        <dt>Android App</dt>
        <dd>
          {info?.config.android_app && <CopyableKitDescription kit={info.config.android_app} />}
        </dd>
        <dt>Registry App</dt>
        <dd>
          {info?.config.registry_app && <CopyableKitDescription kit={info.config.registry_app} />}
        </dd>
      </DescriptionList>

      <H4>Parameters</H4>
      <DescriptionList margin pending={isLoading} striped weight={4}>
        <dt>Config Encryption</dt>
        <dd>{info?.config.race_encryption_type}</dd>
        <dt>Host AWS Environment</dt>
        <dd>{info?.config.aws_env_name}</dd>
      </DescriptionList>
    </>
  );
};
