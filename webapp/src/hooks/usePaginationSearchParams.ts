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

import { useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

const toInt = (arg: string | null, def: number): number =>
  arg != null ? Number.parseInt(arg) : def;

export type UsePaginationSearchParamsOptions = {
  initialPage?: number;
  initialSize?: number;
  pageKey?: string;
  sizeKey?: string;
};

export type UsePaginationSearchParamsResult = {
  page: number;
  setPage: (arg: number) => void;
  setSize: (arg: number) => void;
  setPagination: ({ page, size }: { page: number; size: number }) => void;
  size: number;
};

export const usePaginationSearchParams = ({
  initialPage = 1,
  initialSize = 20,
  pageKey = 'page',
  sizeKey = 'size',
}: UsePaginationSearchParamsOptions = {}): UsePaginationSearchParamsResult => {
  const [searchParams, setSearchParams] = useSearchParams();

  const page = toInt(searchParams.get(pageKey), initialPage);
  const size = toInt(searchParams.get(sizeKey), initialSize);

  const setPage = useCallback(
    (arg: number) => {
      searchParams.set(pageKey, String(arg));
      setSearchParams(searchParams);
    },
    [pageKey, searchParams, setSearchParams]
  );
  const setSize = useCallback(
    (arg: number) => {
      searchParams.set(sizeKey, String(arg));
      setSearchParams(searchParams);
    },
    [sizeKey, searchParams, setSearchParams]
  );
  const setPagination = useCallback(
    ({ page, size }: { page: number; size: number }) => {
      searchParams.set(pageKey, String(page));
      searchParams.set(sizeKey, String(size));
      setSearchParams(searchParams);
    },
    [pageKey, sizeKey, searchParams, setSearchParams]
  );

  return {
    page,
    setPage,
    setSize,
    setPagination,
    size,
  };
};
