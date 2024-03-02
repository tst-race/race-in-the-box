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

import { Button, Menu, MenuDivider, MenuItem } from '@blueprintjs/core';
import { Popover2, Tooltip2 } from '@blueprintjs/popover2';
import { useMemo } from 'react';

type FilterOption = {
  text: string;
  value: string;
};

export type NodeFilterOptionsProps<T> = {
  minimal?: boolean;
  onChange: (option: T | null) => void;
  options: string[] | FilterOption[] | Record<string, string>;
  text: string;
  value: string | null;
};

function normalize(options: string[] | FilterOption[] | Record<string, string>): FilterOption[] {
  if (Array.isArray(options)) {
    return options.map((option) =>
      typeof option == 'string' ? { text: option, value: option } : option
    );
  }
  return Object.entries(options).map(([key, value]) => ({ text: value, value: key }));
}

export const FilterToolbarButton = <T extends string | null>({
  minimal = false,
  onChange,
  options,
  text,
  value,
}: NodeFilterOptionsProps<T>) => {
  const filterOptions = useMemo(() => normalize(options), [options]);

  const menu = (
    <Menu>
      {minimal && <MenuDivider title={text} />}
      <MenuItem icon={value ? 'blank' : 'tick'} onClick={() => onChange(null)} text="All" />
      {filterOptions.map((option) => (
        <MenuItem
          key={option.value}
          icon={option.value == value ? 'tick' : 'blank'}
          onClick={() => onChange(option.value as T)}
          text={option.text}
        />
      ))}
    </Menu>
  );

  return (
    <Popover2 content={menu} placement="bottom-start">
      <Tooltip2
        content={text}
        disabled={!minimal}
        openOnTargetFocus={false}
        placement="bottom-start"
        usePortal={false}
      >
        <Button
          icon={value ? 'filter' : undefined}
          rightIcon="caret-down"
          small
          text={minimal ? `${text[0]}...` : text}
        />
      </Tooltip2>
    </Popover2>
  );
};
