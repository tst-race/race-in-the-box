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

import { Button } from '@blueprintjs/core';

import { useDisclosure } from '@/hooks/useDisclosure';

import { RequestFactsProps } from './RequestFacts/RequestFacts';
import { RequestFactsDialog } from './RequestFactsDialog';

export const RequestFactsButton = (props: RequestFactsProps) => {
  const { isOpen, open, close } = useDisclosure();
  return (
    <>
      <Button icon="more" minimal onClick={open} />
      <RequestFactsDialog isOpen={isOpen} onClose={close} {...props} />
    </>
  );
};
