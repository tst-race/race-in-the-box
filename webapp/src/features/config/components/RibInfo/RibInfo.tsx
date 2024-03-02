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

import { Classes, Text } from '@blueprintjs/core';
import clsx from 'clsx';

import { RIB_VERSION } from '@/config';

import { useRibInfo } from '../../api/getRibInfo';

import styles from './RibInfo.module.css';

type HeadingProps = {
  as: keyof JSX.IntrinsicElements;
  text: string;
};

const Heading = ({ as: Component, text }: HeadingProps) => (
  <Component className={clsx(Classes.HEADING, styles.heading)}>{text}</Component>
);

type ItemProps = {
  as: keyof JSX.IntrinsicElements;
  isLoading?: boolean;
  name: string;
  value?: string;
};

const Item = ({ as: Component, isLoading = false, name, value = '' }: ItemProps) => (
  <>
    <Component className={Classes.HEADING}>{name}</Component>
    <Text className={clsx({ [Classes.SKELETON]: isLoading })} ellipsize>
      {value}
    </Text>
  </>
);

export const RibInfo = () => {
  const { data, isLoading } = useRibInfo();

  return (
    <div className={clsx(Classes.DIALOG_BODY, styles.ribInfo)}>
      <Heading as="h3" text="Client:" />
      <Item as="h4" name="Version:" value={RIB_VERSION} />

      <Heading as="h3" text="Server:" />
      <Item as="h4" isLoading={isLoading} name="Version:" value={data?.version} />

      <Heading as="h4" text="Image:" />
      <Item as="h5" isLoading={isLoading} name="Tag:" value={data?.image_tag} />
      <Item as="h5" isLoading={isLoading} name="Digest:" value={data?.image_digest} />
      <Item as="h5" isLoading={isLoading} name="Created:" value={data?.image_created} />
    </div>
  );
};
