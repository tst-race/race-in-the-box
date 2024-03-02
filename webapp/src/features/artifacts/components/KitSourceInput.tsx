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
import { FieldPath, PathValue, UseFormSetValue } from 'react-hook-form';

import { TextInput, TextInputProps } from '@/components/Forms';
import { useDisclosure } from '@/hooks/useDisclosure';

import { KitSourceWizardDialog } from './KitSourceWizardDialog';

export type KitSourceInputProps<Inputs, TFieldName extends FieldPath<Inputs>> = TextInputProps<
  Inputs,
  TFieldName
> & {
  allowCore?: boolean;
  setValue: UseFormSetValue<Inputs>;
};

export const KitSourceInput = <
  Inputs,
  TFieldName extends FieldPath<Inputs>,
  TFieldValue extends PathValue<Inputs, TFieldName>
>({
  allowCore = true,
  error,
  id,
  inputProps = {},
  label,
  register,
  setValue,
}: KitSourceInputProps<Inputs, TFieldName>) => {
  const dialog = useDisclosure();
  return (
    <>
      <TextInput error={error} id={id} inputProps={inputProps} label={label} register={register}>
        <Button icon="search" id={`${id}-search`} onClick={dialog.open} />
      </TextInput>
      <KitSourceWizardDialog
        allowCore={allowCore}
        isOpen={dialog.isOpen}
        onClose={dialog.close}
        onSelect={(value) => setValue<TFieldName>(id, value as TFieldValue)}
      />
    </>
  );
};
