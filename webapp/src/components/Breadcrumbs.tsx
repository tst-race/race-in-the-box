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

import {
  Breadcrumbs as BpBreadcrumbs,
  BreadcrumbProps as BpBreadcrumbProps,
} from '@blueprintjs/core';
import React from 'react';
import { useNavigate, NavigateOptions, To } from 'react-router-dom';

export type BreadcrumbProps = Omit<BpBreadcrumbProps, 'href'> & {
  navOptions?: NavigateOptions;
  to: To;
};

export type BreadcrumbsProps = {
  items: BreadcrumbProps[];
};

export const Breadcrumbs = ({ items }: BreadcrumbsProps) => {
  const navigate = useNavigate();
  const itemsWithOnClick = React.useMemo(
    () =>
      items.map(({ navOptions, to, ...item }) => ({
        ...item,
        onClick: () => navigate(to, navOptions),
      })),
    [items, navigate]
  );
  return <BpBreadcrumbs items={itemsWithOnClick} />;
};
