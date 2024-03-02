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

import { Button, ButtonProps, Spinner, SpinnerSize } from '@blueprintjs/core';
import { RefetchOptions, RefetchQueryFilters, useIsFetching } from '@tanstack/react-query';
import { useCallback } from 'react';

import { queryClient } from '@/lib/react-query';

type RefreshButtonProps = ButtonProps & {
  filters?: RefetchQueryFilters;
  options?: RefetchOptions;
  queryKey: unknown[];
};

export const RefreshButton = ({ filters, options, queryKey, ...props }: RefreshButtonProps) => {
  const isFetching = useIsFetching(queryKey, filters);

  const handleClick = useCallback(
    () => queryClient.refetchQueries(queryKey, filters, options),
    [queryKey, filters, options]
  );

  return (
    <Button
      disabled={isFetching != 0}
      icon={isFetching == 0 ? 'refresh' : <Spinner size={SpinnerSize.SMALL} />}
      onClick={handleClick}
      text="Refresh"
      {...props}
    />
  );
};
