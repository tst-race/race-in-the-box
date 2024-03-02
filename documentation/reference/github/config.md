# Update GitHub Configuration

Set GitHub-related settings used by other RiB commands when interacting with
GitHub.

The default RACE images and RACE core settings apply to the deployment creation
commands. For example, with a default RACE core org and repo, one can omit
the `repo` and `org` parameters from the RACE core source argument.

## Syntax

```sh
rib github config <args>
```

## Example

```sh
rib github config \
    --access-token TOKEN \
    --username USERNAME \
    --default-org tst-race \
    --default-race-images-org tst-race \
    --default-race-images-repo race-images \
    --default-race-images-tag latest \
    --default-race-core-org tst-race \
    --default-race-core-repo race-core \
    --default-race-core-source tag=1.0.0
```

## Arguments

### Required

None

### Optional

`--access-token TEXT`

A personal access token to allow RiB to authenticate with GitHub. This is
required in order to access private GitHub repositories. If this is not
set, rib will only be able to access public GitHub repositories and an error
will occur if it attempts to access a private repository.

This token can be created by following these steps:
1. Login to [`github.com`](https://github.com/)
   * Alternatively, follow [this link](https://github.com/settings/tokens/new) and skip to step 6
1. Go to "Settings" via the top-right user avatar dropdown menu
1. Go to "Developer settings" via the left-hand side bar (you may need to scroll down to see it)
1. Go to "Personal access tokens" then "Tokens (classic)" via the left-hand
   side bar
1. Click the "Generate new token" button (choose the classic option when
   prompted)
1. Select the "repo" and "read:packages" scope
1. Click the "Generate token" button

`--username TEXT`

The GitHub username to be used when authenticating with the GitHub container
registry. This is required in order to pull Docker images from private GitHub
repositories. If this is not set, rib will only be able to use public Docker
images and an error will occur if it attempts to use images from a private
repository.

`--default-org TEXT`

The name of the GitHub organization, or owner, to use by default for images or
when fetching kits from GitHub when no explicit org is specified. If this is
not set and an explicit org is not specified for an image or kit source, an
error will occur.

`--default-race-images-org TEXT`

The name of the GitHub organization, or owner, to use by default for image
names in the GitHub container registry when no explicit org is specified. If
this is not set, the value set for `--default-org` will be used.

`--default-race-images-repo TEXT`

The name of the GitHub repository to use by default for image names in the
GitHub container registry when no explicit repo is specified. If this is not
set, the default will be `race-images`.

`--default-race-images-tag TEXT`

The tag to use by default for images when no explicit tag is specified. If this
is not set, the default will be `latest`.

`--default-race-core-org TEXT`

The name of the GitHub organization, or owner, to use by default for fetching
RACE core kits from GitHub when no explicit org is specified. If this is not
set, the value set for `--default-org` will be used.

`--default-race-core-repo TEXT`

The name of the GitHub repository to use by default for fetching RACE core kits
from GitHub when no explicit repo is specified. If this is not set, the default
will be `race-core`.

`--default-race-core-source TEXT`

The RACE core source to use by default for fetching RACE core kits when no
explicit RACE core source is specified. If this is not set and no explicit RACE
core source is specified, an error will occur.

The value supplied must satisfy the same constraints as the `--race-core`
argument to other rib commands (e.g., `tag=x.y.z`, `branch=main`).
