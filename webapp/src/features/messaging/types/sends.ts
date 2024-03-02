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

export type SendAutoRequest = {
  message_period: number;
  message_quantity: number;
  message_size: number;
  recipient?: string;
  sender?: string;
  test_id?: string;
  network_manager_bypass_route?: string;
  verify?: boolean;
  timeout?: number;
};

export type SendManualRequest = {
  message_content: string;
  recipient?: string;
  sender?: string;
  test_id?: string;
  network_manager_bypass_route?: string;
  verify?: boolean;
  timeout?: number;
};
