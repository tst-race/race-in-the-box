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

import { faker } from '@faker-js/faker';

import { loadApiSpec } from '@/test/openApiSpec';

import {
  ActiveDeployment,
  AppStatusValues,
  ArtifactsStatusValues,
  BootstrapNodeRequest,
  ConfigGenerationParameters,
  ConfigsStatusValues,
  ContainerStatusReport,
  ContainerStatusValues,
  DaemonStatusValues,
  DeploymentsList,
  EtcStatusValues,
  LocalDeploymentCreateRequest,
  LocalDeploymentInfo,
  NodeOperationRequest,
  NodeStatusValues,
  ParentNodeStatusReport,
  RaceStatusValues,
  ServiceStatusReport,
  ServiceStatusValues,
  StandUpLocalDeploymentRequest,
} from './index';

loadApiSpec();

test('ActiveDeployment matches spec', () => {
  const payload: ActiveDeployment = {
    name: faker.datatype.string(),
  };
  expect(payload).toSatisfySchemaInApiSpec('ActiveDeployment');
});

test.each(Object.keys(AppStatusValues).map((v) => [v]))(
  'AppStatus %p matches spec',
  (payload: string) => expect(payload).toSatisfySchemaInApiSpec('AppStatus')
);

test.each(Object.keys(ArtifactsStatusValues).map((v) => [v]))(
  'ArtifactsStatus %p matches spec',
  (payload: string) => expect(payload).toSatisfySchemaInApiSpec('ArtifactsStatus')
);

test.each(Object.keys(ConfigsStatusValues).map((v) => [v]))(
  'ConfigsStatus %p matches spec',
  (payload: string) => expect(payload).toSatisfySchemaInApiSpec('ConfigsStatus')
);

test.each(Object.keys(DaemonStatusValues).map((v) => [v]))(
  'DaemonStatus %p matches spec',
  (payload: string) => expect(payload).toSatisfySchemaInApiSpec('DaemonStatus')
);

test.each(Object.keys(EtcStatusValues).map((v) => [v]))(
  'EtcStatus %p matches spec',
  (payload: string) => expect(payload).toSatisfySchemaInApiSpec('EtcStatus')
);

test.each(Object.keys(RaceStatusValues).map((v) => [v]))(
  'RaceStatus %p matches spec',
  (payload: string) => expect(payload).toSatisfySchemaInApiSpec('RaceStatus')
);

test.each(Object.keys(NodeStatusValues).map((v) => [v]))(
  'NodeStatus %p matches spec',
  (payload: string) => expect(payload).toSatisfySchemaInApiSpec('NodeStatus')
);

test('ParentNodeStatusReport matches spec', () => {
  const payload: ParentNodeStatusReport = {
    status: 'SOME_RUNNING',
    reason: faker.datatype.string(),
    children: {
      [faker.datatype.string()]: {
        status: 'READY_TO_INSTALL_CONFIGS',
        reason: faker.datatype.string(),
        children: {
          app: {
            status: 'NOT_INSTALLED',
            reason: faker.datatype.string(),
            children: {},
          },
          artifacts: {
            status: 'ARTIFACTS_EXIST',
            reason: faker.datatype.string(),
            children: {},
          },
          configs: {
            status: 'EXTRACTED_CONFIGS',
            reason: faker.datatype.string(),
            children: {},
          },
          daemon: {
            status: 'NOT_REPORTING',
            reason: faker.datatype.string(),
            children: {},
          },
          etc: {
            status: 'READY',
            reason: faker.datatype.string(),
            children: {},
          },
          race: {
            status: 'NETWORK_MANAGER_NOT_READY',
            reason: faker.datatype.string(),
            children: {},
          },
        },
      },
    },
  };
  expect(payload).toSatisfySchemaInApiSpec('ParentNodeStatusReport');
});

test.each(Object.keys(ContainerStatusValues).map((v) => [v]))(
  'ContainerStatus %p matches spec',
  (payload: string) => expect(payload).toSatisfySchemaInApiSpec('ContainerStatus')
);

test('ContainerStatusReport matches spec', () => {
  const payload: ContainerStatusReport = {
    status: 'SOME_RUNNING',
    reason: faker.datatype.string(),
    children: {
      [faker.datatype.string()]: {
        status: 'STARTING',
        reason: faker.datatype.string(),
        children: {},
      },
    },
  };
  expect(payload).toSatisfySchemaInApiSpec('ParentContainerStatusReport');
});

test('DeploymentsList matches spec', () => {
  const payload: DeploymentsList = {
    compatible: [{ name: faker.datatype.string() }],
    incompatible: [{ name: faker.datatype.string(), rib_version: faker.system.semver() }],
  };
  expect(payload).toSatisfySchemaInApiSpec('DeploymentsList');
});

test('LocalDeploymentCreateRequest matches spec', () => {
  const payload: LocalDeploymentCreateRequest = {
    name: faker.datatype.string(),
    race_core: faker.datatype.string(),
    network_manager_kit: faker.datatype.string(),
    comms_channels: [faker.datatype.string()],
    comms_kits: [faker.datatype.string()],
    android_app: faker.datatype.string(),
    linux_app: faker.datatype.string(),
    node_daemon: faker.datatype.string(),
    artifact_manager_kits: [faker.datatype.string()],
    android_client_image: faker.datatype.string(),
    linux_client_image: faker.datatype.string(),
    linux_server_image: faker.datatype.string(),
    range_config: {
      range: {
        name: faker.datatype.string(),
        bastion: { range_ip: faker.datatype.string() },
        RACE_nodes: [],
        enclaves: [],
        services: [],
      },
    },
    fetch_plugins_on_start: faker.datatype.boolean(),
    no_config_gen: faker.datatype.boolean(),
    disable_config_encryption: faker.datatype.boolean(),
    enable_gpu: faker.datatype.boolean(),
    cache: faker.datatype.string(),
    race_log_level: faker.datatype.string(),
  };
  expect(payload).toSatisfySchemaInApiSpec('CreateLocalDeploymentParams');
});

test('LocalDeploymentInfo matches spec', () => {
  const payload: LocalDeploymentInfo = {
    config: {
      android_app: {
        name: faker.datatype.string(),
        kit_type: 'core',
        source: {
          source_type: 'core',
          raw: faker.datatype.string(),
        },
      },
      android_container_acceleration: faker.datatype.boolean(),
      artifact_manager_kits: [
        {
          name: faker.datatype.string(),
          kit_type: 'artifact-manager',
          source: {
            source_type: 'remote',
            raw: faker.datatype.string(),
          },
        },
      ],
      comms_channels: [
        {
          name: faker.datatype.string(),
          kit_name: faker.datatype.string(),
          enabled: faker.datatype.boolean(),
        },
      ],
      comms_kits: [
        {
          name: faker.datatype.string(),
          kit_type: 'comms',
          source: {
            source_type: 'gh_tag',
            raw: faker.datatype.string(),
          },
        },
      ],
      es_metadata_index: faker.datatype.string(),
      host_env_config: {
        host_os: faker.datatype.string(),
        platform: faker.datatype.string(),
        docker_engine_version: faker.system.semver(),
        systemd_version: faker.system.semver(),
        gpu_support: faker.datatype.boolean(),
        adb_support: faker.datatype.boolean(),
        adb_compatible: faker.datatype.boolean(),
        dev_kvm_support: faker.datatype.boolean(),
      },
      images: [
        {
          architecture: 'arm64-v8a',
          node_type: 'client',
          platform: 'android',
          tag: faker.datatype.string(),
        },
        {
          architecture: 'x86_64',
          node_type: 'client',
          platform: 'linux',
          tag: faker.datatype.string(),
        },
        {
          architecture: 'x86_64',
          node_type: 'server',
          platform: 'linux',
          tag: faker.datatype.string(),
        },
      ],
      linux_app: {
        name: faker.datatype.string(),
        kit_type: 'core',
        source: {
          source_type: 'gh_branch',
          raw: faker.datatype.string(),
        },
      },
      log_metadata_to_es: faker.datatype.boolean(),
      mode: 'local',
      name: faker.datatype.string(),
      network_manager_kit: {
        name: faker.datatype.string(),
        kit_type: 'network-manager',
        source: {
          source_type: 'gh_action_run',
          raw: faker.datatype.string(),
        },
      },
      node_daemon: {
        name: faker.datatype.string(),
        kit_type: 'core',
        source: {
          source_type: 'core',
          raw: faker.datatype.string(),
        },
      },
      nodes: {
        [faker.datatype.string()]: {
          architecture: 'arm64-v8a',
          bridge: faker.datatype.boolean(),
          genesis: faker.datatype.boolean(),
          gpu: faker.datatype.boolean(),
          node_type: 'client',
          platform: 'android',
        },
      },
      race_core: {
        source_type: 'local',
        raw: faker.datatype.string(),
      },
      race_encryption_type: 'ENC_AES',
      registry_app: {
        name: faker.datatype.string(),
        kit_type: 'core',
        source: {
          source_type: 'core',
          raw: faker.datatype.string(),
        },
      },
      rib_version: faker.system.semver(),
      tmpfs_size: faker.datatype.number(),
    },
    metadata: {
      rib_image: {
        image_tag: faker.datatype.string(),
        image_digest: faker.datatype.string(),
        image_created: faker.datatype.string(),
      },
      create_command: faker.datatype.string(),
      create_date: faker.datatype.string(),
      race_core_cache: {
        auth: faker.datatype.boolean(),
        cache_path: faker.system.filePath(),
        checksum: faker.git.commitSha(),
        source_type: 'core',
        source_uri: faker.datatype.string(),
        time: faker.datatype.string(),
      },
      android_app_cache: {
        auth: faker.datatype.boolean(),
        cache_path: faker.system.filePath(),
        checksum: faker.git.commitSha(),
        source_type: 'core',
        source_uri: faker.datatype.string(),
        time: faker.datatype.string(),
      },
      linux_app_cache: {
        auth: faker.datatype.boolean(),
        cache_path: faker.system.filePath(),
        checksum: faker.git.commitSha(),
        source_type: 'core',
        source_uri: faker.datatype.string(),
        time: faker.datatype.string(),
      },
      registry_app_cache: {
        auth: faker.datatype.boolean(),
        cache_path: faker.system.filePath(),
        checksum: faker.git.commitSha(),
        source_type: 'core',
        source_uri: faker.datatype.string(),
        time: faker.datatype.string(),
      },
      node_daemon_cache: {
        auth: faker.datatype.boolean(),
        cache_path: faker.system.filePath(),
        checksum: faker.git.commitSha(),
        source_type: 'core',
        source_uri: faker.datatype.string(),
        time: faker.datatype.string(),
      },
      network_manager_kit_cache: {
        auth: faker.datatype.boolean(),
        cache_path: faker.system.filePath(),
        checksum: faker.git.commitSha(),
        source_type: 'core',
        source_uri: faker.datatype.string(),
        time: faker.datatype.string(),
      },
      comms_kits_cache: {
        [faker.datatype.string()]: {
          auth: faker.datatype.boolean(),
          cache_path: faker.system.filePath(),
          checksum: faker.git.commitSha(),
          source_type: 'core',
          source_uri: faker.datatype.string(),
          time: faker.datatype.string(),
        },
      },
      artifact_manager_kits_cache: {
        [faker.datatype.string()]: {
          auth: faker.datatype.boolean(),
          cache_path: faker.system.filePath(),
          checksum: faker.git.commitSha(),
          source_type: 'core',
          source_uri: faker.datatype.string(),
          time: faker.datatype.string(),
        },
      },
      last_config_gen_command: faker.datatype.string(),
      last_config_gen_time: faker.datatype.string(),
      last_up_command: faker.datatype.string(),
      last_up_time: faker.datatype.string(),
      last_start_command: faker.datatype.string(),
      last_start_time: faker.datatype.string(),
      last_stop_command: faker.datatype.string(),
      last_stop_time: faker.datatype.string(),
      last_down_command: faker.datatype.string(),
      last_down_time: faker.datatype.string(),
    },
  };
  expect(payload).toSatisfySchemaInApiSpec('LocalDeploymentInfo');
});

test.each(Object.keys(ServiceStatusValues).map((v) => [v]))(
  'ServiceStatus %p matches spec',
  (payload: string) => expect(payload).toSatisfySchemaInApiSpec('ServiceStatus')
);

test('ServiceStatusReport matches spec', () => {
  const payload: ServiceStatusReport = {
    status: 'ALL_DOWN',
    reason: faker.datatype.string(),
    children: {
      'External Services': {
        status: 'ALL_RUNNING',
        reason: faker.datatype.string(),
        children: {
          [faker.datatype.string()]: {
            status: 'RUNNING',
            reason: faker.datatype.string(),
            children: {},
          },
        },
      },
      RiB: {
        status: 'ERROR',
        reason: faker.datatype.string(),
        children: {
          [faker.datatype.string()]: {
            status: 'RUNNING',
            reason: faker.datatype.string(),
            children: {},
          },
        },
      },
    },
  };
  expect(payload).toSatisfySchemaInApiSpec('GrandparentServiceStatusReport');
});

test('ConfigGenerationParameters matches spec', () => {
  const payload: ConfigGenerationParameters = {
    network_manager_custom_args: faker.datatype.string(),
    comms_custom_args: {
      [faker.datatype.string()]: faker.datatype.string(),
    },
    artifact_manager_custom_args: {
      [faker.datatype.string()]: faker.datatype.string(),
    },
    force: false,
    skip_config_tar: false,
    timeout: faker.datatype.number(),
    max_iterations: faker.datatype.number(),
  };
  expect(payload).toSatisfySchemaInApiSpec('GenerateConfigParams');
});

test('NodeOperationRequest matches spec', () => {
  const payload: NodeOperationRequest = {
    force: false,
    nodes: null,
    timeout: 300,
  };
  expect(payload).toSatisfySchemaInApiSpec('NodeOperationParams');

  payload.nodes = [faker.datatype.string()];
  expect(payload).toSatisfySchemaInApiSpec('NodeOperationParams');
});

test('StandUpLocalDeploymentRequest matches spec', () => {
  const payload: StandUpLocalDeploymentRequest = {
    force: false,
    nodes: null,
    no_publish: false,
    timeout: 300,
  };
  expect(payload).toSatisfySchemaInApiSpec('StandUpLocalDeploymentParams');

  payload.nodes = [faker.datatype.string()];
  expect(payload).toSatisfySchemaInApiSpec('StandUpLocalDeploymentParams');
});

test('BootstrapNodeRequest matches spec', () => {
  const payload: BootstrapNodeRequest = {
    force: false,
    introducer: faker.datatype.string(),
    target: faker.datatype.string(),
    passphrase: faker.datatype.string(),
    architecture: 'arm64-v8a',
    timeout: 600,
  };
  expect(payload).toSatisfySchemaInApiSpec('BootstrapNodeParams');
});
