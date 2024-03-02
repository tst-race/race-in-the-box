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

import { MenuItem, MenuItemProps } from '@blueprintjs/core';
import { useNavigate, NavigateOptions, To } from 'react-router-dom';

export type NavMenuItemProps = Omit<MenuItemProps, 'onClick'> & {
  disabled?: boolean;
  navOptions?: NavigateOptions;
  to: To;
};

export const NavMenuItem = ({ disabled = false, navOptions, to, ...props }: NavMenuItemProps) => {
  const navigate = useNavigate();
  const handleClick = () => navigate(to, navOptions);
  return <MenuItem disabled={disabled} onClick={handleClick} {...props} />;
};
