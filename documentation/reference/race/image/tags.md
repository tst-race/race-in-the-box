# Tags for a RACE Image

List available tags for a RACE image that are compatible with a particular
version of RACE.

## syntax

```
rib race image tags <args>
```

## example

```
1) rib:x.y.z@code# rib race image tags --image=race-linux-client
rc-x.y.z
x.y.z
2) rib:x.y.z@code#
```

## required args

#### `--image TEXT`

Name of the image for which to query. Must be one of:

* race-in-the-box
* race-base
* race-compile
* race-runtime
* race-ndk
* race-sdk
* race-android-x86_64-client
* race-android-x86_64-client-exemplar
* race-android-x86_64-client-complete
* race-android-arm64-v8a-client
* race-android-arm64-v8a-client-exemplar
* race-android-arm64-v8a-client-complete
* race-linux-client
* race-linux-client-exemplar
* race-linux-client-complete
* race-linux-server
* race-linux-server-exemplar
* race-linux-server-complete

## optional args

#### `--race TEXT`

*Default: latest version of RACE*

Which version of RACE for which to list tags

#### `--env TEXT`

*Default: prod*

Environment in which to search for tags. Must be one of:

* dev
* prod
