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

import { Card, Classes } from '@blueprintjs/core';
import clsx from 'clsx';
import { useNavigate, NavigateOptions, To } from 'react-router-dom';

import styles from './NavCard.module.css';

export type NavCardProps = {
  text: string;
  to: To;
  navOptions?: NavigateOptions;
  secondaryText?: string;
  skeleton?: boolean;
};

export const NavCard = ({
  text,
  to,
  navOptions,
  secondaryText,
  skeleton = false,
}: NavCardProps) => {
  const navigate = useNavigate();
  const handleClick = () => navigate(to, navOptions);
  return (
    <Card
      className={clsx(styles.card, { [Classes.SKELETON]: skeleton })}
      interactive
      onClick={handleClick}
    >
      <div className={styles.content}>
        <span>{text}</span>
        {secondaryText && <span>{secondaryText}</span>}
      </div>
    </Card>
  );
};
