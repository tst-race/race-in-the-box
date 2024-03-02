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

import { Button, ControlGroup, InputGroup, NumericInput } from '@blueprintjs/core';
import { useEffect } from 'react';
import { SubmitHandler, useForm } from 'react-hook-form';

import { Switch } from '@/components/Forms';
import { queryClient } from '@/lib/react-query';

import { messagingKeys } from '../api/queryKeys';
import { MessageListFilter } from '../types';

import { MessageListProps } from './MessageList/MessageList';

type Inputs = MessageListFilter;

type Keys =
  | 'recipient'
  | 'sender'
  | 'test_id'
  | 'trace_id'
  | 'date_from'
  | 'date_to'
  | 'reverse_sort'
  | 'size';

const defaultValues: Inputs = {
  recipient: '',
  sender: '',
  test_id: '',
  trace_id: '',
  date_from: '',
  date_to: '',
  reverse_sort: false,
  size: 50,
};

export type MessageListFilterInputProps = {
  filters: MessageListFilter | undefined;
  setFilters: (filters: MessageListFilter | null) => void;
} & MessageListProps;

export const MessageListFilterInput = ({
  filters,
  setFilters,
  mode,
  name,
}: MessageListFilterInputProps) => {
  const form = useForm<Inputs>({ defaultValues });

  useEffect(() => {
    form.reset(filters || defaultValues);
  }, [filters, form.reset]);

  const onSubmit: SubmitHandler<Inputs> = (inputs) => {
    queryClient.invalidateQueries(messagingKeys.listAll(mode, name));
    setFilters(inputs);
  };

  const { ref: recipientRef, ...recipientProps } = form.register('recipient');
  const { ref: senderRef, ...senderProps } = form.register('sender');
  const { ref: testIDRef, ...testIDProps } = form.register('test_id');
  const { ref: traceIDRef, ...traceIDProps } = form.register('trace_id');
  const { ref: dateFromRef, ...dateFromProps } = form.register('date_from');
  const { ref: dateToRef, ...dateToProps } = form.register('date_to');
  const { ref: reverseSortRef, ...reverseSortProps } = form.register('reverse_sort');
  const { ref: sizeRef, ...sizeProps } = form.register('size');

  const handleClear = () => form.reset(defaultValues);

  const rightElement = (specific_filter: Keys | undefined) =>
    specific_filter ? (
      <Button icon="cross" minimal onClick={() => specificClear(specific_filter)} />
    ) : undefined;
  const specificClear = (toClear: Keys) => form.setValue(toClear, '');

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <ControlGroup vertical={true}>
        <InputGroup
          fill
          inputRef={recipientRef}
          placeholder="Receiver Node Filter..."
          rightElement={rightElement(filters?.recipient ? 'recipient' : undefined)}
          {...recipientProps}
        />
        <InputGroup
          fill
          inputRef={senderRef}
          placeholder="Sender Node Filter..."
          rightElement={rightElement(filters?.sender ? 'sender' : undefined)}
          {...senderProps}
        />
        <InputGroup
          fill
          inputRef={testIDRef}
          placeholder="Test ID Filter..."
          rightElement={rightElement(filters?.test_id ? 'test_id' : undefined)}
          {...testIDProps}
        />
        <InputGroup
          fill
          inputRef={traceIDRef}
          placeholder="Trace ID Filter..."
          rightElement={rightElement(filters?.trace_id ? 'trace_id' : undefined)}
          {...traceIDProps}
        />
        <InputGroup
          fill
          inputRef={dateFromRef}
          placeholder="Date From Filter..."
          rightElement={rightElement(filters?.date_from ? 'date_from' : undefined)}
          {...dateFromProps}
        />
        <InputGroup
          fill
          inputRef={dateToRef}
          placeholder="Date To Filter..."
          rightElement={rightElement(filters?.date_to ? 'date_to' : undefined)}
          {...dateToProps}
        />
        <Switch label="Reverse Sort" inputRef={reverseSortRef} {...reverseSortProps} />
        <NumericInput
          placeholder="# of Results/Page"
          inputRef={sizeRef}
          {...sizeProps}
          min={10}
          max={500}
        />
        <Button icon="search" type="submit" />
        {filters ? <Button icon="cross" minimal onClick={handleClear} /> : undefined}
      </ControlGroup>
    </form>
  );
};
