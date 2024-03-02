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

import { Classes, Menu, MenuDivider, MenuItem } from '@blueprintjs/core';
import clsx from 'clsx';
import { FaGithub } from 'react-icons/fa';

import { useDisclosure } from '@/hooks/useDisclosure';

import { NavMenuItem } from '../NavMenuItem';

import { NavGroup } from './NavGroup';
import styles from './Sidebar.module.css';

export const Sidebar = () => {
  const { isOpen, toggle } = useDisclosure(true);

  return (
    <div className={clsx(Classes.ELEVATION_2, styles.sidebar, { [styles.collapsed]: !isOpen })}>
      <Menu>
        <NavGroup icon="gantt-chart" text="Operations" isOpen={isOpen} to="/operations">
          <NavMenuItem icon="gantt-chart" text="Operations Queue" to="/operations" />
        </NavGroup>
        <NavGroup icon="desktop" text="Local Deployments" isOpen={isOpen} to="/deployment/local">
          <NavMenuItem icon="desktop" text="Dashboard" to="/deployments/local" />
          <NavMenuItem icon="add" text="Create" to="/deployments/local/create" />
        </NavGroup>
        <NavGroup icon="cloud" text="AWS Deployments" isOpen={isOpen} to="/deployments/aws">
          <NavMenuItem disabled icon="cloud" text="Dashboard" to="/deployments/aws" />
          <NavMenuItem disabled icon="add" text="Create" to="/deployments/aws/create" />
        </NavGroup>
        <NavGroup icon="cog" text="Settings" isOpen={isOpen} to="/config/github">
          <NavMenuItem icon={<FaGithub />} text="GitHub Configuration" to="/config/github" />
          <NavMenuItem icon="saved" text="Templates" to="/templates" />
          <NavMenuItem disabled icon="cloud" text="AWS Configuration" to="/config/aws" />
        </NavGroup>
      </Menu>
      <Menu className={styles.collapseMenu}>
        <MenuDivider />
        <MenuItem
          icon={isOpen ? 'double-chevron-left' : 'double-chevron-right'}
          text="Collapse Sidebar"
          onClick={toggle}
        />
      </Menu>
    </div>
  );
};
