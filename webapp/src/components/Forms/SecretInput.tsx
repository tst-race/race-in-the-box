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

import { Button, Intent } from '@blueprintjs/core';
import React from 'react';

import { TextInput, TextInputProps } from './TextInput';

export const SecretInput = <Inputs,>({ inputProps = {}, ...props }: TextInputProps<Inputs>) => {
  const [showSecret, setShowSecret] = React.useState(false);
  const handleToggle = () => setShowSecret((old) => !old);

  const showButton = (
    <Button
      icon={showSecret ? 'eye-open' : 'eye-off'}
      intent={Intent.WARNING}
      minimal
      onClick={handleToggle}
    />
  );

  return (
    <TextInput
      inputProps={{
        ...inputProps,
        rightElement: showButton,
        type: showSecret ? 'text' : 'password',
      }}
      {...props}
    />
  );
};
