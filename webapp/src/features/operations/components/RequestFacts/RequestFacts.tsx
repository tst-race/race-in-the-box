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

import { Classes, H3, H4, Text } from '@blueprintjs/core';
import clsx from 'clsx';

import styles from './RequestFacts.module.css';

const formatQuery = (query: string): string => {
  const params = new URLSearchParams(query);
  let formatted = '';
  params.forEach((value, key) => (formatted += `${key} = ${value}\n`));
  return formatted;
};

const formatBody = (body: string): string => {
  try {
    return JSON.stringify(JSON.parse(body), null, 2);
  } catch (error) {
    return 'Unable to parse as JSON';
  }
};

export type RequestFactsProps = {
  requestMethod: string;
  requestPath: string;
  requestQuery: string;
  requestBody: string;
};

export const RequestFacts = ({
  requestMethod,
  requestPath,
  requestQuery,
  requestBody,
}: RequestFactsProps) => {
  return (
    <div className={clsx(Classes.DIALOG_BODY, styles.requestFacts)}>
      <H3>Request:</H3>
      <H4>Method:</H4>
      <pre>{requestMethod}</pre>
      <H4>Path:</H4>
      <pre>{requestPath}</pre>
      <H4>Query:</H4>
      <Text ellipsize tagName="pre">
        {requestQuery}
      </Text>
      <H4>Query Params:</H4>
      <pre>{formatQuery(requestQuery)}</pre>
      <H4>Body (raw):</H4>
      <Text ellipsize tagName="pre">
        {requestBody}
      </Text>
      <H4>Body (json):</H4>
      <pre>{formatBody(requestBody)}</pre>
    </div>
  );
};
