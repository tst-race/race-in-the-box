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

import { Alert, AlertProps, Button, ButtonProps } from '@blueprintjs/core';
import { MouseEvent, ReactNode } from 'react';

import { useDisclosure } from '@/hooks/useDisclosure';

type ConfirmationButtonProps = ButtonProps & {
  alertProps?: Partial<AlertProps>;
  prompt: ReactNode;
};

export const ConfirmationButton = ({
  alertProps,
  intent,
  onClick,
  prompt,
  ...props
}: ConfirmationButtonProps) => {
  const { close, isOpen, open } = useDisclosure();
  const handleConfirm = (event: MouseEvent<HTMLElement>) => {
    if (onClick) {
      onClick(event);
    }
    close();
  };

  return (
    <>
      <Button intent={intent} onClick={open} {...props} />
      <Alert
        canEscapeKeyCancel
        canOutsideClickCancel
        intent={intent}
        isOpen={isOpen}
        onCancel={close}
        onConfirm={handleConfirm}
        {...alertProps}
      >
        {prompt}
      </Alert>
    </>
  );
};
