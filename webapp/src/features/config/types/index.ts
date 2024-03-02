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

export type RibInfo = {
  version: string;
  image_tag: string;
  image_digest: string;
  image_created: string;
};

export type GitHubConfig = {
  access_token: string;
  username: string;
  default_org: string;
  default_race_images_org: string;
  default_race_images_repo: string;
  default_race_images_tag: string;
  default_race_core_org: string;
  default_race_core_repo: string;
  default_race_core_source: string;
};
