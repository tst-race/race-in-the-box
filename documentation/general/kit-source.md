# Kit Sources

In RACE, a kit is a bundle of 

Several RiB commands--mainly the deployment creation commands--require kit
source arguments in order to specify the locations from which RiB can obtain
network manager, comms, artifact manager, or app kits.

## Kit Contents

In general a kit is a tar or zip archive (or for local kits, a plain directory)
containing scripts, manifests, or artifacts. Different kit types require
different sets of files in order for the kit to be considered valid, but in
general the folder structure is consistent across kit types.

### App Kit Contents

An app kit will contain platform-specific artifacts with an Android app or
executable binaries. An Android-only app will not contain any Linux artifact
directories, and a Linux-only app will not contain any Android artifact
directories.

```
./
    app-manifest.json
    artifacts/
        android-arm64-v8a-client/
            appname/
                appname.apk
        android-x86_64-client/
            appname/
                appname.apk
        linux-x86_64-client/
            appname/
                bin/
                lib/
        linux-x86_64-server/
            appname/
                bin/
                lib/
```

The `app-manifest.json` is optional, and can specify the name of the executable
relative to the platform-specific artifact directory. For example, the following
is the app manifest for the core test app:

```json
{
    "executable": "race/bin/racetestapp"
}
```

### Network Manager Kit Contents

A network manager kit will contain config generation scripts and
platform-specific artifacts with the dynamically-loadable plugin.

```
./
    config-generator/
        generate_configs.sh
    artifacts/
        android-arm64-v8a-client/
            PluginName/
                libPluginName.so
                manifest.json
        android-x86_64-client/
            PluginName/
                libPluginName.so
                manifest.json
        linux-x86_64-client/
            PluginName/
                libPluginName.so
                manifest.json
        linux-x86_64-server/
            PluginName/
                libPluginName.so
                manifest.json
```

### Comms Kit Contents

A comms kit will contain channel-specific config generation scripts, external
service scripts, and platform-specific artifacts with the dynamically-loadable
plugin.

```
./
    channels/
        channelName/
            get_status_of_external_services.sh
            start_external_services.sh
            stop_external_services.sh
            generate_configs.sh
    artifacts/
        android-arm64-v8a-client/
            PluginName/
                libPluginName.so
                manifest.json
        android-x86_64-client/
            PluginName/
                libPluginName.so
                manifest.json
        linux-x86_64-client/
            PluginName/
                libPluginName.so
                manifest.json
        linux-x86_64-server/
            PluginName/
                libPluginName.so
                manifest.json
```

The external service scripts are only required if the channel relies on other
Docker containers to be started with a deployment in order for the channel to
function (e.g., communication over a whiteboard service).

### Artifact Manager Kit Contents

An artifact manager kit will contain config generation scripts, external
service scripts, an artifact upload script, and platform-specific artifacts
with the dynamically-loadable plugin.

```
./
    config-generator/
        generate_configs.sh
    runtime-scripts/
        get_status_of_external_services.sh
        start_external_services.sh
        stop_external_services.sh
        upload_artifacts.sh
    artifacts/
        android-arm64-v8a-client/
            PluginName/
                libPluginName.so
                manifest.json
        android-x86_64-client/
            PluginName/
                libPluginName.so
                manifest.json
        linux-x86_64-client/
            PluginName/
                libPluginName.so
                manifest.json
        linux-x86_64-server/
            PluginName/
                libPluginName.so
                manifest.json
```

### RACE Core Kit Contents

When a kit source is specified for a deployment's `--race-core` option, the
"kit" is actually a collection of core kits.

```
./
    plugin-network-manager-twosix-cpp.tar.gz
    plugin-comms-twosix-cpp.tar.gz
    racetestapp-linux.tar.gz
```

## Local Sources

A local kit is one present on the local filesystem and may be the result of
locally building the kit or manually downloading. The local kit source is
specified using the following syntax:

```
--opt=local=<path>
```

Where `<path>` is the path to the directory or archive containing the kit.

For example:

```
rib deployment local create \
    --linux-app local=/code/race-core/racetestapp-linux/kit \
    --comms-kit local=/code/awesome-comms.tar.gz
```

## Remote Sources

A remote kit is one obtained from an arbitrary internet URL. The kit must be a
zip or tar archive, and must be publicly accessible with no authentication
required. The remote kit source is specified using the following syntax:

```
--opt=remote=<url>
```

Where `<url>` is the complete URL to the kit.

For example:

```
rib deployment local create \
    --comms-kit remote=https://awesome-mirror.org/awesome-comms.tar.gz
```

## GitHub Tagged Release Sources

A GitHub tagged release kit is one obtained from a GitHub tag release as an
attached artifact. The kit must be a zip or tar archive. If the GitHub
repository is private, a GitHub access token must have been set by running
`rib github config`. The tag kit source is specified using the following syntax:

```
--opt=tag=<tag>(,org=<org>)(,repo=<repo>)(,asset=<asset>)
--opt=tag=https://github.com/<org>/<repo>/releases/tag/<tag>(,asset=<asset>)
--opt=tag=https://github.com/<org>/<repo>/releases/download/<tag>/<asset>
```

In form 1, the `<repo>` must be specified in addition to the `<tag>` unless the
source is for RACE core (where `<repo>` will default to the one set by running
`rib github config`). `<org>` may be omitted and will default to the one set by
running `rib github config`. If `<asset>` is omitted, it will default to
`<repo>.tar.gz`.

In form 2, the `<org>`, `<repo>`, and `<tag>` are all parsed out of the URL.
This allows for copying and pasting the URL directly out of a browser. If
`<asset>` is omitted, it will default to `<repo>.tar.gz`.

In form 3, all parameters are parsed out of the URL. This allows for copying and
pasting the URL directly out of the browser. This URL is obtained for individual
artifacts attached to a tag release.

For example:

```
rib deployment local create \
    --race-core tag=1.0.0 \
    --comms-kit tag=0.1.0,repo=awesome-comms \
    --comms-kit tag=3.1.4,org=awesome-org,awesome-comms \
    --comms-kit tag=0.0.1,repo=awesome-comms,asset=debug-build.tar.gz \
    --comms-kit tag=https://github.com/awesome-org/awesome-comms/releases/tag/3.1.4 \
    --comms-kit tag=https://github.com/default-org/awesome-comms/releases/download/0.0.1/debug-build.tar.gz
```

In this example,

* RACE core is using the default org and repo
* The first comms kit is using the default org
* The second comms kit is using an explicit org and repo
* The third comms kit is using the default org and an explicit asset
* The fourth comms kit is using explicit org and repo using a tag URL
* The fifth comms kit is using an explicit org, repo, and asset using a tag
  artifact URL.

## GitHub Branch Sources

A GitHub branch kit is one obtained from the latest GitHub Actions run for the
branch as an attached artifact. The kit must be a zip or tar archive. If the
GitHub repository is private, a GitHub access token must have been set by
running `rib github config`. The tag kit source is specified using the following
syntax:

```
--opt=branch=<branch>(,org=<org>)(,repo=<repo>)(,asset=<asset>)
```

Where `<repo>` must be specified in addition to the `<branch>` unless the source
is for RACE core (where `<repo>` will default to the one set by running
`rib github config`). `<org>` may be omitted and will default to the one set by
running `rib github config`. If `<asset>` is omitted, it will default to
`<repo>.tar.gz`.

For example:

```
rib deployment local create \
    --race-core branch=main \
    --comms-kit branch=dev,repo=awesome-comms \
    --comms-kit branch=awesome-branch,org=awesome-org,awesome-comms \
    --comms-kit branch=dev,repo=awesome-comms,asset=debug-build.tar.gz
```

In this example,

* RACE core is using the default org and repo
* The first comms kit is using the default org
* The second comms kit is using an explicit org and repo
* The third comms kit is using the default org and an explicit asset

## GitHub Actions Run Sources

A GitHub Actions run kit is one obtained from a particular GitHub Actions run as
an attached artifact. The kit must be a zip or tar archive. If the GitHub
repository is private, a GitHub access token must have been set by running
`rib github config`. The tag kit source is specified using the following syntax:

```
--opt=run=<runid>(,org=<org>)(,repo=<repo>)(,asset=<asset>)
--opt=run=https://github.com/<org>/<repo>/actions/runs/<runid>(,asset=<asset>)
```

In form 1, the `<repo>` must be specified in addition to the `<runid>` unless
the source is for RACE core (where `<repo>` will default to the one set by
running `rib github config`). `<org>` may be omitted and will default to the one
set by running `rib github config`. If `<asset>` is omitted, it will default to
`<repo>.tar.gz`.

In form 2, the `<org>`, `<repo>`, and `<runid>` are all parsed out of the URL.
This allows for copying and pasting the URL directly out of a browser. If
`<asset>` is omitted, it will default to `<repo>.tar.gz`.

For example:

```
rib deployment local create \
    --race-core run=5017563561 \
    --comms-kit run=8675309123,repo=awesome-comms \
    --comms-kit run=3141592653,org=awesome-org,awesome-comms \
    --comms-kit run=1234567890,repo=awesome-comms,asset=debug-build.tar.gz \
    --comms-kit run=https://github.com/default-org/awesome-comms/actions/runs/5017563561
```

In this example,

* RACE core is using the default org and repo
* The first comms kit is using the default org
* The second comms kit is using an explicit org and repo
* The third comms kit is using the default org and an explicit asset
* The fourth comms kit is using explicit org and repo using an actions run URL

## Core Kit Sources

A core kit is one obtained from RACE core. The kit must be a tar archive, and is
limited to the apps and kits provided by the RACE core specified with
`--race-core`. RACE core can be obtained by any other type of source. A core
kit source is specified using the following syntax:

```
--opt=core=<kit>
--opt=core=<kit>.tar.gz
```

Where `<kit>` is the name of the RACE core kit. The `.tar.gz` extension may be
omitted, as seen in form 1.

For example:

```
rib deployment local create \
    --race-core tag=1.0.0 \
    --comms-kit core=plugin-comms-twosix-cpp \
    --comms-kit core=plugin-comms-twosix-java
```

In this example,

* RACE core is obtained from the GitHub tagged release 1.0.0
* The first comms kit is the C++ exemplar from RACE core
* The second comms kit is the Java exemplar from RACE core
