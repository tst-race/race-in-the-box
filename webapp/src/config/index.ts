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

export const RIB_VERSION = (process.env.REACT_APP_RIB_VERSION as string) || 'dev';

// Feature flags
const isTruthy = (value = 'no') => value in ['true', 'yes', '1'];
export const ENABLE_PORT_MAPPING = isTruthy(process.env.REACT_APP_ENABLE_PORT_MAPPING);
export const ENABLE_TEMPLATES = isTruthy(process.env.REACT_APP_ENABLE_TEMPLATES);
export const ENABLE_AWS_DEPLOYMENTS = isTruthy(process.env.REACT_APP_ENABLE_AWS_DEPLOYMENTS);
