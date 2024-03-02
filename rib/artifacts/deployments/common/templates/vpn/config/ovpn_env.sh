
# Copyright 2023 Two Six Technologies
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 

declare -x OVPN_AUTH=
declare -x OVPN_CIPHER=
declare -x OVPN_CLIENT_TO_CLIENT=1
declare -x OVPN_CN=race
declare -x OVPN_COMP_LZO=0
declare -x OVPN_DEFROUTE=0
declare -x OVPN_DEVICE=tun
declare -x OVPN_DEVICEN=0
declare -x OVPN_DISABLE_PUSH_BLOCK_DNS=1
declare -x OVPN_DNS=1
declare -x OVPN_DNS_SERVERS=([0]="8.8.8.8" [1]="8.8.4.4")
declare -x OVPN_ENV=/etc/openvpn/ovpn_env.sh
declare -x OVPN_EXTRA_CLIENT_CONFIG=()
declare -x OVPN_EXTRA_SERVER_CONFIG=([0]="topology subnet")
declare -x OVPN_FRAGMENT=
declare -x OVPN_KEEPALIVE='10 60'
declare -x OVPN_MTU=
declare -x OVPN_NAT=1
declare -x OVPN_PORT=1194
declare -x OVPN_PROTO=udp
declare -x OVPN_PUSH=([0]="route 10.11.0.0 255.255.255.0" [1]="dhcp-option DNS 10.11.0.250")
declare -x OVPN_ROUTES=([0]="192.168.254.0/24")
declare -x OVPN_SERVER=192.168.255.0/24
declare -x OVPN_SERVER_URL=udp://race
declare -x OVPN_TLS_CIPHER=
