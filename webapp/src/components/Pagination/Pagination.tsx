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

import { Button, ButtonGroup } from '@blueprintjs/core';

/**
 * Create an array of integers from start to stop, inclusive
 * @param start First integer value
 * @param stop Last integer value
 * @returns Array of integers
 */
const createArray = (start: number, stop: number) =>
  [...Array(Math.max(1, stop - start + 1))].map((_, index) => index + start);

export type PaginationProps = {
  pad?: number;
  page: number;
  setPage: (arg: number) => void;
  size: number;
  total: number;
};

export const Pagination = ({ pad = 4, page, setPage, size, total }: PaginationProps) => {
  const totalPages = Math.ceil(total / size);
  // The min and max pages to show surrounding the current, based on padding
  let minSurrPage = Math.max(1, page - pad);
  let maxSurrPage = Math.min(totalPages, page + pad);
  // Number of pages to skip between first/last and the min/max surrounding pages
  let numSkippedPrev = Math.max(0, minSurrPage - 2);
  let numSkippedNext = Math.max(0, totalPages - maxSurrPage - 1);

  // If we're only skipping over one page, just include it as a surrounding page
  if (numSkippedPrev == 1) {
    numSkippedPrev = 0;
    minSurrPage = minSurrPage - 1;
  }
  if (numSkippedNext == 1) {
    numSkippedNext = 0;
    maxSurrPage = maxSurrPage + 1;
  }

  return (
    <ButtonGroup>
      <Button
        disabled={page == 1}
        icon="chevron-left"
        onClick={() => setPage(page - 1)}
        text="Prev"
      />

      {/* link to first page if not part of surrounding pages */}
      {minSurrPage > 1 && <Button onClick={() => setPage(1)} text="1" />}

      {numSkippedPrev > 1 && <Button disabled text="..." />}

      {createArray(minSurrPage, maxSurrPage).map((toPage) => (
        <Button
          key={`${toPage}`}
          intent={toPage == page ? 'primary' : 'none'}
          onClick={() => setPage(toPage)}
          text={`${toPage}`}
        />
      ))}

      {numSkippedNext > 1 && <Button disabled text="..." />}

      {/* link to last page if not part of surrounding pages */}
      {maxSurrPage < totalPages && (
        <Button onClick={() => setPage(totalPages)} text={`${totalPages}`} />
      )}

      <Button
        disabled={page >= totalPages}
        onClick={() => setPage(page + 1)}
        rightIcon="chevron-right"
        text="Next"
      />
    </ButtonGroup>
  );
};
