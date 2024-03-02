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

import { rest } from 'msw';

import {
  ActiveDeployment,
  ContainerStatusReport,
  DeploymentsList,
  LocalDeploymentInfo,
  NodeNameList,
  ParentNodeStatusReport,
  ServiceStatusReport,
} from '@/features/deployments';
import { RangeConfig } from '@/features/range-config';
import { OperationQueuedResult } from '@/types';

const localDeployments: DeploymentsList = {
  compatible: [
    { name: 'local-deployment-a' },
    { name: 'local-deployment-b' },
    { name: 'local-deployment-c' },
  ],
  incompatible: [{ name: 'local-deployment-d', rib_version: 'old-rib-version' }],
};

const activeLocalDeployment: ActiveDeployment = {
  name: 'local-deployment-b',
};

const localDeploymentInfo: LocalDeploymentInfo = {
  config: {
    android_app: {
      name: 'AndroidApp',
      kit_type: 'core',
      source: {
        raw: 'core=raceclient-android',
        source_type: 'core',
        asset: 'raceclient-android',
      },
    },
    artifact_manager_kits: [
      {
        name: 'PluginArtifactManagerTwoSixStub',
        kit_type: 'artifact-manager',
        source: {
          raw: 'core=plugin-artifact-manager-twosix-cpp',
          source_type: 'core',
          asset: 'plugin-artifact-manager-twosix-cpp',
        },
      },
    ],
    comms_channels: [
      {
        name: 'twoSixDirectCpp',
        kit_name: 'PluginCommsTwoSixStub',
        enabled: true,
      },
      {
        name: 'twoSixIndirectCpp',
        kit_name: 'PluginCommsTwoSixStub',
        enabled: true,
      },
    ],
    comms_kits: [
      {
        name: 'PluginCommsTwoSixStub',
        kit_type: 'comms',
        source: {
          raw: 'core=plugin-comms-twosix-cpp',
          source_type: 'core',
          asset: 'plugin-comms-twosix-cpp',
        },
      },
    ],
    es_metadata_index: '',
    images: [
      {
        architecture: 'x86_64',
        node_type: 'client',
        platform: 'linux',
        tag: '2.3.0',
      },
    ],
    linux_app: {
      name: 'LinuxApp',
      kit_type: 'core',
      source: {
        raw: 'core=racetestapp-linux',
        source_type: 'core',
        asset: 'racetestapp-linux',
      },
    },
    log_metadata_to_es: true,
    mode: 'local',
    name: 'local-deployment-with-info',
    network_manager_kit: {
      name: 'PluginNMTwoSixStub',
      kit_type: 'network-manager',
      source: {
        raw: 'core=plugin-network-manager-twosix-cpp',
        source_type: 'core',
        asset: 'plugin-network-manager-twosix-cpp',
      },
    },
    node_daemon: {
      name: 'NodeDaemon',
      kit_type: 'core',
      source: {
        raw: 'core=race-node-daemon',
        source_type: 'core',
        asset: 'race-node-daemon',
      },
    },
    nodes: {
      'race-client-00001': {
        architecture: 'x86_64',
        bridge: false,
        genesis: true,
        gpu: false,
        node_type: 'client',
        platform: 'linux',
      },
      'race-client-00002': {
        architecture: 'auto',
        bridge: true,
        genesis: false,
        gpu: false,
        node_type: 'client',
        platform: 'android',
      },
      'race-server-00001': {
        architecture: 'x86_64',
        bridge: false,
        genesis: true,
        gpu: true,
        node_type: 'server',
        platform: 'linux',
      },
      'race-server-00002': {
        architecture: 'x86_64',
        bridge: false,
        genesis: true,
        gpu: true,
        node_type: 'server',
        platform: 'linux',
      },
    },
    race_core: {
      raw: 'branch=main',
      source_type: 'gh_branch',
      org: 'gh-org',
      repo: 'gh-repo',
      branch: 'main',
      asset: 'race-core',
    },
    race_encryption_type: 'ENC_AES',
    rib_version: '2.3.0',
    android_container_acceleration: false,
    host_env_config: {
      host_os: 'Linux',
      platform: 'x86_64',
      docker_engine_version: '20.10.18',
      systemd_version: '245',
      gpu_support: false,
      adb_support: true,
      adb_compatible: true,
      dev_kvm_support: true,
    },
    tmpfs_size: 0,
  },
  metadata: {
    rib_image: {
      image_tag: '2.3.0',
      image_digest: 'deadbeef',
      image_created: 'yesterday',
    },
    create_command: 'created by UI',
    create_date: 'today',
    race_core_cache: {
      auth: false,
      cache_path: '/cache/race-core',
      checksum: 'deadbeef',
      source_type: 'gh_branch',
      source_uri: 'https://github.com/gh-org/gh-repo',
      time: '2023-05-16T13:13:13',
    },
    android_app_cache: {
      auth: false,
      cache_path: '/cache/race-core-android-app',
      checksum: 'deadbeef',
      source_type: 'gh_branch',
      source_uri: 'https://github.com/gh-org/gh-repo',
      time: '2023-05-16T13:13:13',
    },
    linux_app_cache: {
      auth: false,
      cache_path: '/cache/race-core-linux-app',
      checksum: 'deadbeef',
      source_type: 'gh_branch',
      source_uri: 'https://github.com/gh-org/gh-repo',
      time: '2023-05-16T13:13:13',
    },
    node_daemon_cache: {
      auth: false,
      cache_path: '/cache/race-core-node-daemon',
      checksum: 'deadbeef',
      source_type: 'gh_branch',
      source_uri: 'https://github.com/gh-org/gh-repo',
      time: '2023-05-16T13:13:13',
    },
    network_manager_kit_cache: {
      auth: false,
      cache_path: '/cache/race-core-plugin-network-manager-twosix-cpp',
      checksum: 'deadbeef',
      source_type: 'gh_branch',
      source_uri: 'https://github.com/gh-org/gh-repo',
      time: '2023-05-16T13:13:13',
    },
    comms_kits_cache: {
      PluginCommsTwoSixStub: {
        auth: false,
        cache_path: '/cache/race-core-plugin-comms-twosix-cpp',
        checksum: 'deadbeef',
        source_type: 'gh_branch',
        source_uri: 'https://github.com/gh-org/gh-repo',
        time: '2023-05-16T13:13:13',
      },
    },
    artifact_manager_kits_cache: {
      PluginArtifactManagerTwoSixCpp: {
        auth: false,
        cache_path: '/cache/race-core-plugin-artifact-manager-twosix-cpp',
        checksum: 'deadbeef',
        source_type: 'gh_branch',
        source_uri: 'https://github.com/gh-org/gh-repo',
        time: '2023-05-16T13:13:13',
      },
    },
  },
};

const localDeploymentRangeConfig: RangeConfig = {
  range: {
    name: 'stub-local-range-config',
    bastion: { range_ip: '' },
    RACE_nodes: [
      {
        name: 'race-client-00001',
        type: 'client',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: true,
        gpu: false,
        bridge: false,
        platform: 'linux',
        architecture: 'x86_64',
        environment: 'any',
      },
      {
        name: 'race-client-00002',
        type: 'client',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: false,
        gpu: false,
        bridge: false,
        platform: 'linux',
        architecture: 'x86_64',
        environment: 'any',
      },
      {
        name: 'race-client-00003',
        type: 'client',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: true,
        gpu: false,
        bridge: false,
        platform: 'android',
        architecture: 'x86_64',
        environment: 'phone',
      },
      {
        name: 'race-client-00004',
        type: 'client',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: false,
        gpu: false,
        bridge: false,
        platform: 'android',
        architecture: 'arm64-v8a',
        environment: 'phone',
      },
      {
        name: 'race-client-00005',
        type: 'client',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: false,
        gpu: false,
        bridge: true,
        platform: 'android',
        architecture: 'auto',
        environment: 'phone',
      },
      {
        name: 'race-client-00006',
        type: 'client',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: false,
        gpu: false,
        bridge: true,
        platform: 'android',
        architecture: 'auto',
        environment: 'phone',
      },
      {
        name: 'race-server-00001',
        type: 'server',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: true,
        gpu: false,
        bridge: false,
        platform: 'linux',
        architecture: 'x86_64',
        environment: 'any',
      },
      {
        name: 'race-server-00002',
        type: 'server',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: true,
        gpu: false,
        bridge: false,
        platform: 'linux',
        architecture: 'x86_64',
        environment: 'any',
      },
      {
        name: 'race-server-00003',
        type: 'server',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: true,
        gpu: false,
        bridge: false,
        platform: 'linux',
        architecture: 'x86_64',
        environment: 'any',
      },
      {
        name: 'race-server-00004',
        type: 'server',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: true,
        gpu: false,
        bridge: false,
        platform: 'linux',
        architecture: 'x86_64',
        environment: 'any',
      },
      {
        name: 'race-server-00005',
        type: 'server',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: true,
        gpu: false,
        bridge: false,
        platform: 'linux',
        architecture: 'x86_64',
        environment: 'any',
      },
      {
        name: 'race-server-00006',
        type: 'server',
        enclave: 'global',
        nat: false,
        identities: [],
        genesis: true,
        gpu: false,
        bridge: false,
        platform: 'linux',
        architecture: 'x86_64',
        environment: 'any',
      },
    ],
    enclaves: [],
    services: [],
  },
};

const localDeploymentNodeStatus: ParentNodeStatusReport = {
  children: {
    'race-client-00001': {
      children: {
        daemon: { status: 'NOT_REPORTING' },
        app: { status: 'NOT_REPORTING' },
        race: { status: 'NOT_REPORTING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'ERROR_CONFIG_GEN_FAILED' },
        etc: { status: 'MISSING_REQUIRED_FILES' },
      },
      status: 'READY_TO_GENERATE_CONFIG',
    },
    'race-client-00002': {
      children: {
        daemon: { status: 'NOT_REPORTING' },
        app: { status: 'NOT_REPORTING' },
        race: { status: 'NOT_REPORTING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'CONFIG_GEN_SUCCESS' },
        etc: { status: 'CONFIG_GEN_SUCCESS' },
      },
      status: 'READY_TO_TAR_CONFIGS',
    },
    'race-client-00003': {
      children: {
        daemon: { status: 'NOT_REPORTING' },
        app: { status: 'NOT_REPORTING' },
        race: { status: 'NOT_REPORTING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'CONFIGS_TAR_EXISTS' },
        etc: { status: 'ETC_TAR_EXISTS' },
      },
      status: 'DOWN',
    },
    'race-client-00004': {
      children: {
        daemon: { status: 'RUNNING' },
        app: { status: 'NOT_RUNNING' },
        race: { status: 'NOT_REPORTING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'CONFIGS_TAR_EXISTS' },
        etc: { status: 'ETC_TAR_EXISTS' },
      },
      status: 'READY_TO_PUBLISH_CONFIGS',
    },
    'race-client-00005': {
      children: {
        daemon: { status: 'RUNNING' },
        app: { status: 'NOT_RUNNING' },
        race: { status: 'NOT_REPORTING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'CONFIGS_TAR_PUSHED' },
        etc: { status: 'ETC_TAR_PUSHED' },
      },
      status: 'READY_TO_INSTALL_CONFIGS',
    },
    'race-client-00006': {
      children: {
        daemon: { status: 'RUNNING' },
        app: { status: 'NOT_INSTALLED' },
        race: { status: 'NOT_REPORTING' },
        artifacts: { status: 'ARTIFACT_TARS_EXIST' },
        configs: { status: 'DOWNLOADED_CONFIGS' },
        etc: { status: 'READY' },
      },
      status: 'READY_TO_BOOTSTRAP',
    },
    'race-server-00001': {
      children: {
        daemon: { status: 'RUNNING' },
        app: { status: 'NOT_RUNNING' },
        race: { status: 'NOT_REPORTING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'DOWNLOADED_CONFIGS' },
        etc: { status: 'READY' },
      },
      status: 'READY_TO_START',
    },
    'race-server-00002': {
      children: {
        daemon: { status: 'RUNNING' },
        app: { status: 'RUNNING' },
        race: { status: 'NETWORK_MANAGER_NOT_READY' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'EXTRACTED_CONFIGS' },
        etc: { status: 'READY' },
      },
      status: 'INITIALIZING',
    },
    'race-server-00003': {
      children: {
        daemon: { status: 'RUNNING' },
        app: { status: 'RUNNING' },
        race: { status: 'RUNNING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'EXTRACTED_CONFIGS' },
        etc: { status: 'READY' },
      },
      status: 'RUNNING',
    },
    'race-server-00004': {
      children: {
        daemon: { status: 'RUNNING' },
        app: { status: 'NOT_RUNNING' },
        race: { status: 'RUNNING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'EXTRACTED_CONFIGS' },
        etc: { status: 'READY' },
      },
      status: 'STOPPED',
    },
    'race-server-00005': {
      children: {
        daemon: { status: 'RUNNING' },
        app: { status: 'ERROR' },
        race: { status: 'RUNNING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'EXTRACTED_CONFIGS' },
        etc: { status: 'READY' },
      },
      status: 'ERROR',
    },
    'race-server-00006': {
      children: {
        daemon: { status: 'RUNNING' },
        app: { status: 'NOT_INSTALLED' },
        race: { status: 'RUNNING' },
        artifacts: { status: 'ARTIFACTS_EXIST' },
        configs: { status: 'EXTRACTED_CONFIGS' },
        etc: { status: 'READY' },
      },
      status: 'UNKNOWN',
    },
  },
  status: 'some running',
};

const localDeploymentContainerStatus: ContainerStatusReport = {
  children: {
    'race-client-00001': { status: 'NOT_PRESENT' },
    'race-client-00002': { status: 'STARTING' },
    'race-client-00003': { status: 'UNHEALTHY' },
    'race-client-00004': { status: 'EXITED' },
    'race-server-00001': { status: 'UNKNOWN' },
    'race-server-00002': { status: 'RUNNING' },
    'race-server-00003': { status: 'RUNNING' },
    'race-server-00004': { status: 'RUNNING' },
    'race-server-00005': { status: 'RUNNING' },
    'race-server-00006': { status: 'RUNNING' },
    elasticsearch: { status: 'STARTING', reason: 'Failing healthcheck' },
  },
  status: 'some up',
};

const localDeploymentServiceStatus: ServiceStatusReport = {
  status: 'some up',
  children: {
    'External Services': {
      status: 'all down',
      children: {
        'twosix-whiteboard': { status: 'NOT_RUNNING' },
        'twosix-redis': { status: 'ERROR' },
      },
    },
    RiB: {
      status: 'some up',
      children: {
        elasticsearch: { status: 'RUNNING' },
        'rib-file-server': { status: 'UNKNOWN' },
      },
    },
  },
};

const awsDeployments: DeploymentsList = {
  compatible: [],
  incompatible: [],
};

const activeAwsDeployment: ActiveDeployment = {
  name: '',
};

const bootstrappableNodes: NodeNameList = {
  nodes: ['race-client-00006', 'race-client-00010'],
};

const runningNodes: NodeNameList = {
  nodes: ['race-client-00004', 'race-client-00005', 'race-server-00003'],
};

const noNodes: NodeNameList = {
  nodes: [],
};

const operationQueued: OperationQueuedResult = {
  id: 3,
};

export const localDeploymentHandlers = [
  rest.get('/api/deployments/local', (req, res, ctx) => res(ctx.json(localDeployments))),
  rest.post('/api/deployments/local', (req, res, ctx) => res(ctx.json(operationQueued))),
  rest.get('/api/deployments/local/active', (req, res, ctx) =>
    res(ctx.json(activeLocalDeployment))
  ),
  rest.get(/\/api\/deployments\/local\/.*\/info/, (req, res, ctx) =>
    res(ctx.json(localDeploymentInfo), ctx.delay(250))
  ),
  rest.get(/\/api\/deployments\/local\/.*\/range-config/, (req, res, ctx) =>
    res(ctx.json(localDeploymentRangeConfig), ctx.delay(1000))
  ),
  rest.get(/\/api\/deployments\/local\/.*\/status\/nodes/, (req, res, ctx) =>
    res(ctx.json(localDeploymentNodeStatus), ctx.delay(2000))
  ),
  rest.get(/\/api\/deployments\/local\/.*\/status\/containers/, (req, res, ctx) =>
    res(ctx.json(localDeploymentContainerStatus), ctx.delay(3000))
  ),
  rest.get(/\/api\/deployments\/local\/.*\/status\/services/, (req, res, ctx) =>
    res(ctx.json(localDeploymentServiceStatus), ctx.delay(2500))
  ),
  rest.get(/\/api\/deployments\/local\/.*\/nodes/, (req, res, ctx) => {
    if (req.url.searchParams.get('app') == 'NOT_INSTALLED') {
      return res(ctx.json(bootstrappableNodes), ctx.delay(1000));
    }
    if (req.url.searchParams.get('app') == 'RUNNING') {
      return res(ctx.json(runningNodes), ctx.delay(1000));
    }
    return res(ctx.json(noNodes), ctx.delay(1000));
  }),
  rest.post(/\/api\/deployments\/local\/.*\/operations\/.*/, (req, res, ctx) =>
    res(ctx.json(operationQueued))
  ),
  rest.get('/api/deployments/aws', (req, res, ctx) =>
    res(ctx.json(awsDeployments), ctx.delay(2000))
  ),
  rest.get('/api/deployments/aws/active', (req, res, ctx) =>
    res(ctx.json(activeAwsDeployment), ctx.delay(2000))
  ),
];
