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

import { Intent, IToaster } from '@blueprintjs/core';

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace jest {
    interface Matchers<R, T> {
      toHaveDangerToast: T extends IToaster
        ? (message?: string) => R
        : 'Type-level Error: Received value must be an IToaster';
      toHaveSuccessToast: T extends IToaster
        ? (message?: string) => R
        : 'Type-level Error: Received value must be an IToaster';
    }
  }
}

const toHaveToast = (toaster: IToaster, intent: Intent, message?: string) => {
  const toasts = toaster.getToasts();
  for (const toast of toasts) {
    if (toast.intent == intent) {
      if (message == null || toast.message == message) {
        return {
          message: () => `expected not to have ${intent} toast ${message || ''}`,
          pass: true,
        };
      }
    }
  }
  return {
    message: () => `expected to have ${intent} toast ${message || ''}`,
    pass: false,
  };
};

expect.extend({
  toHaveDangerToast(toaster: IToaster, message?: string) {
    return toHaveToast(toaster, Intent.DANGER, message);
  },
  toHaveSuccessToast(toaster: IToaster, message: string) {
    return toHaveToast(toaster, Intent.SUCCESS, message);
  },
});
