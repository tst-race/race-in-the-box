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

import { useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { Page } from '@/components/Page';
import { DeploymentMode } from '@/features/deployments';

import { MessageList } from '../components/MessageList';

export type MessageListPageProp = {
  mode: DeploymentMode;
};

export const MessageListPage = ({ mode }: MessageListPageProp) => {
  const { name } = useParams();
  const breadcrumbs = useMemo(
    () => [
      { text: `${mode} deployments`, to: '../../..' },
      { text: name, to: '../..' },
      { text: 'List Messages', to: '.' },
    ],
    [mode, name]
  );

  return (
    <Page breadcrumbs={breadcrumbs} title={`${mode}:${name} List Messages`}>
      {mode && name && <MessageList mode={mode} name={name as string} />}
    </Page>
  );
};
