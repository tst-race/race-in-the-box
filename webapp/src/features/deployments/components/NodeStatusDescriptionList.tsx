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

import { DescriptionList } from '@/components/DescriptionList';

import {
  AppStatusValues,
  ArtifactsStatusValues,
  ConfigsStatusValues,
  DaemonStatusValues,
  EtcStatusValues,
  NodeStatusReport,
  RaceStatusValues,
} from '../types';

type NodeStatusDescriptionListProps = {
  status: NodeStatusReport;
};

export const NodeStatusDescriptionList = ({ status }: NodeStatusDescriptionListProps) => (
  <DescriptionList>
    <dt>App</dt>
    <dd>{AppStatusValues[status.children.app.status]}</dd>
    <dt>Artifacts</dt>
    <dd>{ArtifactsStatusValues[status.children.artifacts.status]}</dd>
    <dt>Configs</dt>
    <dd>{ConfigsStatusValues[status.children.configs.status]}</dd>
    <dt>Daemon</dt>
    <dd>{DaemonStatusValues[status.children.daemon.status]}</dd>
    <dt>Etc</dt>
    <dd>{EtcStatusValues[status.children.etc.status]}</dd>
    <dt>RACE</dt>
    <dd>{RaceStatusValues[status.children.race.status]}</dd>
  </DescriptionList>
);
