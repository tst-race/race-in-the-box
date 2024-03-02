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

import { Button, Intent, Spinner, SpinnerSize } from '@blueprintjs/core';
import { yupResolver } from '@hookform/resolvers/yup';
import { SubmitHandler, useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import * as yup from 'yup';

import { ActionButtons } from '@/components/ActionButtons';
import { TextInput, Switch, NumericInput } from '@/components/Forms';
import { DeploymentMode } from '@/features/deployments';

import { useSendAutoMessages } from '../../api/messageSendAuto';
import { SendAutoRequest } from '../../types/sends';
type Inputs = SendAutoRequest;

const defaultValues: Inputs = {
  message_period: 0,
  message_quantity: 1,
  message_size: 1,
  recipient: '',
  sender: '',
  test_id: '',
  network_manager_bypass_route: '',
  verify: false,
  timeout: 0,
};

export const schema = yup.object().shape({
  message_period: yup.number().required().min(0),
  message_quantity: yup.number().required().integer().min(1, 'Quantity must be greater than 0'),
  message_size: yup.number().integer().min(1, 'Size must be greater than 0'),
  recipient: yup.string(),
  sender: yup.string(),
  test_id: yup.string(),
  network_manager_bypass_route: yup.string(),
  verify: yup.boolean(),
  timeout: yup.number().integer().min(0, 'Timeout must be at least 0'),
});

export type MessageSendAutoFormProps = {
  mode: DeploymentMode;
  name: string;
};

export const MessageSendAutoForm = ({ mode, name }: MessageSendAutoFormProps) => {
  const send = useSendAutoMessages();
  const navigate = useNavigate();

  const {
    control,
    formState: { errors },
    handleSubmit,
    register,
    watch,
  } = useForm<Inputs>({ defaultValues, resolver: yupResolver(schema) });

  const onSubmit: SubmitHandler<Inputs> = (data: Inputs) => {
    send.mutate(
      { mode, name, data },
      {
        onSuccess: (result) => navigate(`/operations/${result.id}`),
      }
    );
  };

  const watchVerify = watch('verify');

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <NumericInput control={control} id="message_period" label="Message Period" min={0} />
      <NumericInput control={control} id="message_quantity" label="Message Quantity" min={1} />
      <NumericInput control={control} id="message_size" label="Message Size" min={1} />
      <TextInput
        error={errors.recipient}
        id="recipient"
        label="Message Recipient"
        register={register}
        required={false}
      />
      <TextInput
        error={errors.sender}
        id="sender"
        label="Message Sender"
        register={register}
        required={false}
      />
      <TextInput
        error={errors.test_id}
        id="test_id"
        label="Message Test-ID"
        register={register}
        required={false}
      />
      <TextInput
        error={errors.network_manager_bypass_route}
        id="network_manager_bypass_route"
        label="Network Manager Bypass Route"
        register={register}
        required={false}
      />
      <Switch
        id="verify"
        label="Verify Messages Are Received By Recipients"
        {...register('verify')}
      />
      <NumericInput
        control={control}
        id="timeout"
        label="Message Send Verification Timeout"
        inputProps={{ disabled: !watchVerify }}
        required={false}
        min={0}
      />

      <ActionButtons>
        <Button onClick={() => navigate(-1)} text="Cancel" />
        <Button disabled={send.isLoading} intent={Intent.PRIMARY} type="submit">
          {send.isLoading ? <Spinner size={SpinnerSize.SMALL} /> : 'Send Message'}
        </Button>
      </ActionButtons>
    </form>
  );
};
