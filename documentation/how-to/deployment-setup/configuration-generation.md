# Configuration Generation

<!-- toc -->

  * [Diagrams:](#diagrams)
  * [Configuration Protocol:](#configuration-protocol)
  * [Range-Config:](#range-config)
  * [Network Manager Requesting Links:](#network-manager-requesting-links)
  * [Comms Plugin Link Fulfillment:](#comms-plugin-link-fulfillment)

<!-- tocstop -->

In building a stable RACE network, the BAA states that there will be "A minimal amount of external communications is allowed for initializing the system.". To simplify bootstrapping in phase 2, there will be an assumption that there is some "Genesis Network" which is preconfigured before runtime and deployed with the RACE application. these configuration files are generated offline by ingesting:

- A `range-config` file which defines the physical network 
- Network manager channel/link requests
- Comms channel/link fulfillment

The flow and protocols building these configs and the Genesis network are defined below

Note on the dynamism of the network; once the genesis network has been deployed and RACE is in a stable state, links will need to be generated/removed dynamically utilizing the RACE SDK and APIs.

## Diagrams:

![An image of a force-directed graph](https://github.com/tst-race/race-in-the-box/blob/2.6.0/documentation/files-images-templates/genesis_link_generation.png?raw=true)


## Configuration Protocol:
The process of generating a genesis config is defined in the following steps:

1. The range-config.json has all required information for each comms channel to generate functional links
   1. Network Manager plugins ingest the range-config.json and construct an overlay network that would create a stable and functional RACE network 
1. Network Manager plugins choose comms links to populate connectivity for the generated overlay network in step 2 by generating a network-manager-link-request.json file for each selected channel with connectivity defined 
   1. RIB inputs this file to each comms plugin
1. Each comms plugin ingests the network-manager-link-request.json file for its specific channel and the range-config.json. The comms plugin determines what links it can generate and provide at runtime and generates a fulfilled-network-manager-request.json 
1. If the comms plugin responses are not satisfactory, the network manager plugin can continue to iterate by producing new network-manager-link-request.json files
1. The network manager plugin signals successful configuration generation by writing a network-manager-config-gen-status.json file with: `{"status": "complete", "reason": "succes"}`

## Range-Config:
The range-config.json file describes the physical network, internode connectivity, and external RACE services. This file describes the foundation of the network and plugins ingest this as the source of truth for what nodes can communicate with what ports/protocols.

<details>
<summary>Example updated 2x4 range-config.json:</summary>

```
{
  "range": {
    "name": "Example2x4",
    "bastion": {},
    "RACE_nodes": [
      {
        "name": "race-client-00001",
        "type": "RACE android client",
        "enclave": "Enclave3",
        "nat": true,
        "identities": [
          {
            "email": "race-client-00001@race-client-00001.race-client-00001",
            "password": "password1234",
            "service": "imagegram",
            "username": "race-client-00001"
          }
        ]
      },
      {
        "name": "race-client-00002",
        "type": "RACE linux client",
        "enclave": "Enclave4",
        "nat": true,
        "identities": [
          {
            "email": "race-client-00002@race-client-00002.race-client-00002",
            "password": "password1234",
            "service": "imagegram",
            "username": "race-client-00002"
          }
        ]
      },
      {
        "name": "race-server-00001",
        "type": "RACE linux server",
        "enclave": "Enclave1",
        "nat": false,
        "identities": [
          {
            "email": "race-server-00001@race-server-00001.race-server-00001",
            "password": "password1234",
            "service": "imagegram",
            "username": "race-server-00001"
          }
        ]
      },
      {
        "name": "race-server-00002",
        "type": "RACE linux server",
        "enclave": "Enclave1",
        "nat": false,
        "identities": [
          {
            "email": "race-server-00002@race-server-00002.race-server-00002",
            "password": "password1234",
            "service": "imagegram",
            "username": "race-server-00002"
          }
        ]
      },
      {
        "name": "race-server-00003",
        "type": "RACE linux server",
        "enclave": "Enclave2",
        "nat": true,
        "identities": [
          {
            "email": "race-server-00003@race-server-00003.race-server-00003",
            "password": "password1234",
            "service": "imagegram",
            "username": "race-server-00003"
          }
        ]
      },
      {
        "name": "race-server-00004",
        "type": "RACE linux server",
        "enclave": "Enclave2",
        "nat": true,
        "identities": [
          {
            "email": "race-server-00004@race-server-00004.race-server-00004",
            "password": "password1234",
            "service": "imagegram",
            "username": "race-server-00004"
          }
        ]
      }
    ],
    "enclaves": [
      {
        "name": "Enclave1",
        "ip": "1.2.3.4",
        "port_mapping": {
          "80": {
            "hosts": [
              "race-server-00001",
              "race-server-00002"
            ],
            "port": "80"
          }
        }
      },
      {
        "name": "Enclave2",
        "ip": "2.3.4.5",
        "port_mapping": {
          "8080": {
            "hosts": [
              "race-server-00003"
            ],
            "port": "80"
          },
          "8081": {
            "hosts": [
              "race-server-00004"
            ],
            "port": "80"
          }
        }
      },
      {
        "name": "Enclave3",
        "ip": "3.4.5.6",
        "port_mapping": {}
      },
      {
        "name": "Enclave4",
        "ip": "4.5.6.7",
        "port_mapping": {}
      }
    ],
    "services": [
      {
        "access": [
          {
            "protocol": "http",
            "url": "twosix-whiteboard:5000"
          }
        ],
        "auth-req-post": "anonymous",
        "auth-req-reply": "anonymous",
        "auth-req-view": "anonymous",
        "auth-req_delete": "anonymous",
        "name": "twosix-whiteboard",
        "type": "twosix-whiteboard"
      },
      {
        "access": [
          {
            "protocol": "https",
            "url": "race.example2"
          }
        ],
        "auth-req-post": "authenticate",
        "auth-req-reply": "anonymous",
        "auth-req-view": "anonymous",
        "auth-req_delete": "authenticate",
        "name": "imagegram",
        "type": "social-pixelfed"
      }
    ]
  }
}
```

</details>

## Network Manager Requesting Links:

<details>
<summary>Example link request to a comms plugin to create a fully connected set of 4 servers with multicast links</summary>

```
{
    "links": [
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00002",
                "race-server-00003",
                "race-server-00004"
            ],
            "sender": "race-server-00001"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001",
                "race-server-00003",
                "race-server-00004"
            ],
            "sender": "race-server-00002"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001",
                "race-server-00002",
                "race-server-00004"
            ],
            "sender": "race-server-00003"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001",
                "race-server-00002",
                "race-server-00003"
            ],
            "sender": "race-server-00004"
        }
    ]
}
```
</details>

<details>
<summary>Example link request to create a fully connected set of 4 servers with unicast links</summary>

```
{
    "links": [
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00002"
            ],
            "sender": "race-server-00001"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00003"
            ],
            "sender": "race-server-00001"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00004"
            ],
            "sender": "race-server-00001"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001"
            ],
            "sender": "race-server-00002"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00003"
            ],
            "sender": "race-server-00002"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00004"
            ],
            "sender": "race-server-00002"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001"
            ],
            "sender": "race-server-00003"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00002"
            ],
            "sender": "race-server-00003"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00004"
            ],
            "sender": "race-server-00003"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001"
            ],
            "sender": "race-server-00004"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00002"
            ],
            "sender": "race-server-00004"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00003"
            ],
            "sender": "race-server-00004"
        }
    ]
}
```

</details>

## Comms Plugin Link Fulfillment:
Response from comms plugin should match the format of request. The links that can be fulfilled should be included in the list and details/groupId should be passed through from the network manager request.

<details>
<summary>Example Fulfilled Multicast Requests</summary>

```
{
    "links": [
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00002",
                "race-server-00003",
                "race-server-00004"
            ],
            "sender": "race-server-00001"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001",
                "race-server-00003",
                "race-server-00004"
            ],
            "sender": "race-server-00002"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001",
                "race-server-00002",
                "race-server-00004"
            ],
            "sender": "race-server-00003"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001",
                "race-server-00002",
                "race-server-00003"
            ],
            "sender": "race-server-00004"
        }
    ]
}
```

</details>


<details>
<summary>Example Fulfilled Unicast Requests</summary>

```
{
    "links": [
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00002"
            ],
            "sender": "race-server-00001"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00003"
            ],
            "sender": "race-server-00001"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00004"
            ],
            "sender": "race-server-00001"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001"
            ],
            "sender": "race-server-00002"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00003"
            ],
            "sender": "race-server-00002"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00004"
            ],
            "sender": "race-server-00002"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001"
            ],
            "sender": "race-server-00003"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00002"
            ],
            "sender": "race-server-00003"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00004"
            ],
            "sender": "race-server-00003"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00001"
            ],
            "sender": "race-server-00004"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00002"
            ],
            "sender": "race-server-00004"
        },
        {
            "details": {},
            "groupId": null,
            "recipients": [
                "race-server-00003"
            ],
            "sender": "race-server-00004"
        }
    ]
}
```

</details>


## Link Fulfillment Guidelines:
Some rules for link fulfillment to ensure network manager/comms plugin expectations are in alignment

1. Comms plugins must never create a link that enables a client to open a connection to another client (and network managers should not request such links).
1. If a comms plugin cannot create all links in a group, it will not fulfill any links in a group,
1. If the groupId is null, the comms plugin _may_ aggregate link requests if `set(sender + receivers)` for both links is the same.
   1. e.g. two unicast links in opposite directions could be aggregated as a single bidirectional link.
1. If multicast is requested, the comms plugin must not provide links of any other transmission types to fulfill the requests.
   1. e.g. a comms plugin must not create a series of unicast links to fulfill a multicast link.
1. If a unicast link is requested comms plugins may provide a multicast link that is restricted to just those nodes; a comms plugin must not aggregate multiple unicast links into a single multicast link.
1. Link Requests are per-comms-channel.
1. Comms plugins must not create extra connectivity besides what is requested (unless no requests are made, see below).
1. If comms plugins do not receive a link request, they should generate links providing a complete connectivity graph among all clients and servers (except never generating Direct links to/from clients).
