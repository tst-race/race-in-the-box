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

import { Button, Menu, MenuItem, TagInput } from '@blueprintjs/core';
import { Popover2 } from '@blueprintjs/popover2';
import { ReactNode, SyntheticEvent, useMemo, useState } from 'react';

import { useDisclosure } from '@/hooks/useDisclosure';

export type FilterInputProps = {
  availableFilters: Record<string, Record<string, string>>;
  currentFilters: Record<string, string>;
  onSetFilters: (filters: Record<string, string>) => void;
  placeholder?: string;
};

export const FilterInput = ({
  availableFilters,
  currentFilters,
  onSetFilters,
  placeholder,
}: FilterInputProps) => {
  const { isOpen, open, close } = useDisclosure();
  const [selectedFilterKey, setSelectedFilterKey] = useState<string | null>(null);

  const currentFilterTags = useMemo(
    () =>
      Object.keys(currentFilters)
        .sort()
        .map((key) => `${key} = ${availableFilters[key][currentFilters[key]]}`),
    [availableFilters, currentFilters]
  );

  const handleAddFilter = (key: string, value: string) => {
    onSetFilters({
      ...currentFilters,
      [key]: value,
    });
    close();
  };

  const handleRemoveFilter = (value: ReactNode, index: number) => {
    const key = Object.keys(currentFilters).sort()[index];
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { [key]: _, ...rest } = currentFilters;
    onSetFilters(rest);
  };

  const handleClearFilter = () => onSetFilters({});

  const handleClose = (event: SyntheticEvent<HTMLElement>) => {
    if (event && event.type != 'click') {
      close();
    }
  };

  const filterMenu =
    selectedFilterKey == null ? (
      <Menu>
        {Object.keys(availableFilters)
          .filter((key) => !(key in currentFilters))
          .sort()
          .map((key) => (
            <MenuItem key={key} onClick={() => setSelectedFilterKey(key)} text={key} />
          ))}
      </Menu>
    ) : (
      <Menu>
        {Object.keys(availableFilters[selectedFilterKey]).map((key) => (
          <MenuItem
            key={key}
            onClick={() => handleAddFilter(selectedFilterKey, key)}
            text={availableFilters[selectedFilterKey][key]}
          />
        ))}
      </Menu>
    );

  const clearButton =
    Object.keys(currentFilters).length > 0 ? (
      <Button icon="cross" minimal onClick={handleClearFilter} />
    ) : undefined;

  return (
    <>
      <Popover2
        content={filterMenu}
        fill
        isOpen={isOpen}
        minimal
        onClose={handleClose}
        onClosing={() => setSelectedFilterKey(null)}
        placement="bottom-start"
      >
        <TagInput
          inputProps={{
            onClick: open,
          }}
          onRemove={handleRemoveFilter}
          placeholder={placeholder}
          rightElement={clearButton}
          values={currentFilterTags}
        />
      </Popover2>
    </>
  );
};
