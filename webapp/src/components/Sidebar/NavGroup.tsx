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

import { MenuDivider } from '@blueprintjs/core';
import React from 'react';

import { NavMenuItem, NavMenuItemProps } from '../NavMenuItem';

type NavGroupProps = NavMenuItemProps & {
  children: React.ReactNode;
  isOpen: boolean;
};

export const NavGroup = ({ children, isOpen, ...props }: NavGroupProps) => {
  // When sidebar is open, display sub-menus as sibling menu items
  if (isOpen) {
    return (
      <>
        <MenuDivider title={props.text} />
        {children}
      </>
    );
  }
  // Else when closed, display sub-menus in popup menu
  return (
    <NavMenuItem {...props}>
      <MenuDivider title={props.text} />
      {children}
    </NavMenuItem>
  );
};
