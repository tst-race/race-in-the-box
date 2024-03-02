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

"""
Purpose:
    Utilities for plugins and channels
"""

# Python Library Imports
import click
import hashlib
import json
import logging
import re
import os
import shutil
import tarfile
import tempfile
import urllib.parse
import zipfile
from datetime import datetime
from enum import auto, Enum
from pydantic import BaseModel
from typing import List, Optional, Any
from typing_extensions import TypedDict

# Local Python Library Imports
from rib.utils import (
    error_utils,
    general_utils,
    github_utils,
    network_utils,
    rib_utils,
)


###
# Globals
###


logger = logging.getLogger(__name__)
RIB_CONFIG = rib_utils.load_race_global_configs()
CACHE_DIR = RIB_CONFIG.RIB_PATHS["docker"]["plugins-cache"]


###
# Types
###


class CacheStrategy(general_utils.PrettyEnum):
    """Artifact caching strategy"""

    # No caching, forces a re-download of the artifact
    NEVER = auto()
    # Always use a cached copy of the artifact
    ALWAYS = auto()
    # Use cached copy, unless revision is "latest"
    AUTO = auto()


class KitSourceType(str, Enum):
    """RACE kit source type"""

    CORE = "core"
    LOCAL = "local"
    REMOTE = "remote"
    GH_TAG = "gh_tag"
    GH_BRANCH = "gh_branch"
    GH_ACTION_RUN = "gh_action_run"


class KitSource(BaseModel):
    """RACE kit source data"""

    raw: str
    source_type: KitSourceType
    uri: Optional[str]
    org: Optional[str]
    repo: Optional[str]
    asset: Optional[str]
    tag: Optional[str]
    branch: Optional[str]
    run: Optional[str]

    def __str__(self) -> str:
        return self.raw


class KitType(str, Enum):
    """RACE kit type"""

    NETWORK_MANAGER = "network-manager"
    COMMS = "comms"
    ARTIFACT_MANAGER = "artifact-manager"
    APP = "core"


class KitConfig(BaseModel):
    """RACE kit"""

    name: str
    kit_type: KitType
    source: KitSource


class KitCacheMetadata(BaseModel):
    """RACE kit cache metadata"""

    source_type: KitSourceType
    source_uri: str
    auth: bool
    time: str
    cache_path: str
    checksum: str


###
# Static Functions
###


def apply_race_core_defaults(source: KitSource) -> KitSource:
    """
    Purpose:
        Apply sane defaults to the given RACE core source

    Args:
        source: RACE core source

    Returns:
        RACE core source
    """

    if source.source_type not in [KitSourceType.LOCAL, KitSourceType.REMOTE]:
        if not source.org:
            source.org = github_utils.default_race_core_org()
        if not source.repo:
            source.repo = github_utils.default_race_core_repo()
    return source


def apply_kit_defaults(source: KitSource) -> KitSource:
    """
    Purpose:
        Apply sane defaults to the given RACE kit source

    Args:
        source: RACE kit source

    Returns:
        RACE kit source
    """

    if source.source_type not in [
        KitSourceType.CORE,
        KitSourceType.LOCAL,
        KitSourceType.REMOTE,
    ]:
        if not source.org:
            source.org = github_utils.default_org()
    return source


def parse_kit_source(raw: str) -> KitSource:
    """
    Purpose:
        Parses the raw source string containing a RACE kit source

    Args:
        raw: Raw RACE kit source string

    Returns:
        RACE kit source
    """

    if not raw:
        raise error_utils.RIB500(raw, "empty source string")

    if "," not in raw and "=" not in raw:
        raise error_utils.RIB500(raw, "malformed source string")

    source = dict(source_type=None, raw=raw)
    for key_value_str in raw.split(","):
        key_value_pair = key_value_str.split("=")
        if len(key_value_pair) != 2:
            raise error_utils.RIB500(raw, f"parameter is invalid: {key_value_str}")
        key = key_value_pair[0]
        value = key_value_pair[1]

        if key == "core":
            if source["source_type"] is not None:
                raise error_utils.RIB500(raw, "source contains incompatible paramters")
            source["source_type"] = KitSourceType.CORE
            source["asset"] = value
            if not value.endswith(".tar.gz"):
                source["asset"] = f"{value}.tar.gz"

        elif key == "local":
            if source["source_type"] is not None:
                raise error_utils.RIB500(raw, "source contains incompatible paramters")
            source["source_type"] = KitSourceType.LOCAL
            source["uri"] = value

        elif key == "remote":
            if source["source_type"] is not None:
                raise error_utils.RIB500(raw, "source contains incompatible paramters")
            source["source_type"] = KitSourceType.REMOTE
            source["uri"] = value

        elif key == "tag":
            if source["source_type"] is not None:
                raise error_utils.RIB500(raw, "source contains incompatible paramters")
            source["source_type"] = KitSourceType.GH_TAG
            if "github" in value:
                match = re.match(
                    "^https?://github\.com\/([^/]+)/([^/]+)/releases/(?:tag|download)/([^/]+)/?([^/]+)?$",
                    value,
                )
                if not match:
                    raise error_utils.RIB500(raw, "invalid GitHub release tag URL")
                source["org"] = match.group(1)
                source["repo"] = match.group(2)
                source["tag"] = match.group(3)
                # groups only returns group 1 and above, so a len of 4 means that there are 5 groups
                if len(match.groups()) == 4:
                    source["asset"] = match.group(4)
            else:
                source["tag"] = value

        elif key == "branch":
            if source["source_type"] is not None:
                raise error_utils.RIB500(raw, "source contains incompatible paramters")
            source["source_type"] = KitSourceType.GH_BRANCH
            source["branch"] = value

        elif key == "run":
            if source["source_type"] is not None:
                raise error_utils.RIB500(raw, "source contains incompatible paramters")
            source["source_type"] = KitSourceType.GH_ACTION_RUN
            if "github" in value:
                match = re.match(
                    "^https?://github\.com/([^/]+)/([^/]+)/actions/runs/(\d+)/?.*$",
                    value,
                )
                if not match:
                    raise error_utils.RIB500(raw, "Invalid GitHub Actions run URL")
                source["org"] = match.group(1)
                source["repo"] = match.group(2)
                source["run"] = match.group(3)
            else:
                source["run"] = value

        elif key == "org":
            source["org"] = value

        elif key == "repo":
            source["repo"] = value

        elif key == "asset":
            source["asset"] = value

        else:
            raise error_utils.RIB500(raw, f"parameter key is unrecognized: {key}")

    return KitSource.parse_obj(source)


def download_race_core(
    source: KitSource, cache: CacheStrategy = CacheStrategy.AUTO
) -> KitCacheMetadata:
    """
    Purpose:
        Download the RACE core from the specified source into the local cache

    Args:
        source: RACE core source information
        cache: Cache strategy

    Returns:
        Metadata about downloaded RACE core
    """

    if source.source_type == KitSourceType.CORE:
        raise error_utils.RIB501(
            source.raw,
            "RACE core source must be specified as one of `local`, `remote`, `tag`, "
            "`branch`, or `run`",
        )

    elif source.source_type == KitSourceType.LOCAL:
        return _create_local_cache_metadata(source)

    elif source.source_type == KitSourceType.REMOTE:
        return _download_remote_kit("RACE core", source, cache, True)

    elif source.source_type == KitSourceType.GH_TAG:
        return _download_tag_kit("RACE core", source, cache, True)

    elif source.source_type == KitSourceType.GH_BRANCH:
        return _download_branch_kit("RACE core", source, cache, True)

    elif source.source_type == KitSourceType.GH_ACTION_RUN:
        return _download_action_run_kit("RACE core", source, cache, True)

    else:
        raise error_utils.RIB012(f"Un supported source type: {source.source_type}")


def download_kit(
    kit_type: str,
    source: KitSource,
    race_core: KitCacheMetadata,
    cache: CacheStrategy = CacheStrategy.AUTO,
) -> KitCacheMetadata:
    """
    Purpose:
        Download the RACE kit from the specified source into the local cache

    Args:
        kit_type: Kit type
        source: RACE kit source information
        race_core: RACE core download cache metadata
        cache: Cache strategy

    Returns:
        Metadata about downloaded RACE kit
    """

    if source.source_type == KitSourceType.CORE:
        return _extract_core_kit(kit_type, source, race_core, cache)

    elif source.source_type == KitSourceType.LOCAL:
        return _create_local_cache_metadata(source)
    elif source.source_type == KitSourceType.REMOTE:
        return _download_remote_kit(kit_type, source, cache, True)
    elif source.source_type == KitSourceType.GH_TAG:
        return _download_tag_kit(kit_type, source, cache, True)
    elif source.source_type == KitSourceType.GH_BRANCH:
        return _download_branch_kit(kit_type, source, cache, True)
    elif source.source_type == KitSourceType.GH_ACTION_RUN:
        return _download_action_run_kit(kit_type, source, cache, True)
    else:
        raise error_utils.RIB012(f"Un supported source type: {source.source_type}")


def _now() -> str:
    """Get current time as timestamp string"""

    return datetime.today().strftime("%Y-%m-%d %H:%M:%S")


def _dir_checksum(directory: str) -> str:
    """Get content checksum of the given directory"""
    # TODO: implement me
    return "to-be-implemented"


def _file_checksum(file_path: str) -> str:
    """Get content checksum of the given file"""

    with open(file_path, "rb") as infile:
        file_hash = hashlib.md5()
        while chunk := infile.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()


def _cache_path(*args) -> str:
    """Get cache path from the given segments"""
    encoded = "-".join(args).replace(".", "-")
    return os.path.join(CACHE_DIR, encoded)


def _cache_path_from_uri(uri: str) -> str:
    """Get cache path from the given URI"""
    encoded = urllib.parse.quote(uri).replace("/", "-")
    return os.path.join(CACHE_DIR, encoded)


def _should_cache(cache: CacheStrategy, cache_on_auto: bool) -> bool:
    """
    Purpose:
        Check if cache should be used, based on cache strategy

    Args:
        cache: Cache strategy
        cache_on_auto: Whether the cache should be used when the strategy is auto

    Returns:
        True if cache should be used, else False
    """
    if cache == CacheStrategy.NEVER:
        return False
    elif cache == CacheStrategy.ALWAYS:
        return True
    else:  # auto
        return cache_on_auto


def _read_cached_metadata(cache_path: str) -> Optional[KitCacheMetadata]:
    """
    Purpose:
        Reads the cache metadata from the given cache path

    Args:
        cache_path: Path to cached download folder

    Returns:
        Cache metadata, if it exists
    """

    metadata_file = f"{cache_path}-metadata.json"
    if os.path.exists(metadata_file):
        try:
            return KitCacheMetadata.parse_file(metadata_file)
        except Exception as err:
            logger.error(f"Unable to parse cache metadata file {metadata_file}: {err}")
    return None


def _write_cached_metadata(cache_path: str, metadata: KitCacheMetadata) -> None:
    """
    Purpose:
        Writes the cache metadata for the given cache path

    Args:
        cache_path: Path to cached download folder
        metadata: Cache metadata

    Returns:
        N/A
    """

    metadata_file = f"{cache_path}-metadata.json"
    with open(metadata_file, "w") as out:
        json.dump(metadata.dict(), out, indent=2, sort_keys=True)


def _extract_or_copy_kit(kit_archive: str, dest_path: str, fully_extract: bool) -> None:
    """
    Purpose:
        Extracts (if double-archived) or copy the given RACE kit archive to
        the specified destination

    Args:
        kit_archive: Full path to the RACE kit archive file
        dest_path: Destination path to which to copy the archive
        fully_extract: If True, extract the kit into the destination, else only extract
            the outermost archive and copy the inner archive to the destination

    Returns:
        N/A
    """

    if os.path.exists(dest_path):
        general_utils.remove_dir_file(dest_path)

    if tarfile.is_tarfile(kit_archive):
        with tarfile.open(kit_archive, "r") as tar:
            members = tar.getmembers()
            # If this is an archive within an archive, extract to tmp and recurse
            if len(members) == 1:
                with tempfile.TemporaryDirectory() as tmpdir:
                    tar.extract(members[0], tmpdir)
                    inner_file = os.path.join(tmpdir, members[0].name)
                    _extract_or_copy_kit(inner_file, dest_path, fully_extract)
            elif fully_extract:
                tar.extractall(dest_path)
            else:
                shutil.copyfile(kit_archive, dest_path)
    # We check for zip _after_ tar because the way zipfile.is_zipfile works, it's possible
    # to get false-positives if the tarball _contains_ zip files (like an apk file)
    elif zipfile.is_zipfile(kit_archive):
        with zipfile.ZipFile(kit_archive, "r") as zip:
            entries = zip.infolist()
            # If this is an archive within an archive, extract to tmp and recurse
            if len(entries) == 1:
                with tempfile.TemporaryDirectory() as tmpdir:
                    inner_file = zip.extract(entries[0], tmpdir)
                    _extract_or_copy_kit(inner_file, dest_path, fully_extract)
            elif fully_extract:
                zip.extractall(dest_path)
            else:
                shutil.copyfile(kit_archive, dest_path)
    else:
        raise error_utils.RIB504(kit_archive)


def _extract_core_kit(
    kit_type: str, source: KitSource, race_core: KitCacheMetadata, cache: CacheStrategy
) -> KitCacheMetadata:
    """
    Purpose:
        Extracts (or re-uses cached) kit from RACE core

    Args:
        kit_type: Kit type
        source: Kit source information
        race_core: RACE core cache metadata
        cache: Cache strategy

    Returns:
        Cache metadata
    """

    if not source.asset:
        raise error_utils.RIB501(source.raw, "Core source must specify an asset")

    if race_core.source_type == KitSourceType.LOCAL:
        # If the race-core is local, then its cache path is outside of the internal
        # cache folder, but we want to extract the kit inside the internal cache
        # folder. Have to remove the leading / in the race-core cache path in order
        # to get an internal cache directory.
        cache_path = _cache_path(
            race_core.cache_path[1:].replace("/", "-"), source.asset
        )
    else:
        # race-core's cache is already a directory in the internal plugin-cache folder,
        # so just append the kit asset to form the kit cache path.
        cache_path = "-".join([race_core.cache_path, source.asset.replace(".", "-")])

    # Auto-cache behavior is to not cache when race-core is local or branch
    cache_on_auto = race_core.source_type not in [
        KitSourceType.LOCAL,
        KitSourceType.GH_BRANCH,
    ]
    # Additionally, if source was a branch, check if the extracted cache was from the same
    # workflow run as the downloaded race-core
    cached_download_meta = _read_cached_metadata(cache_path)
    if cached_download_meta and race_core.source_type == KitSourceType.GH_BRANCH:
        cache_on_auto = cached_download_meta.source_uri == race_core.source_uri

    if _should_cache(cache, cache_on_auto=cache_on_auto):
        if cached_download_meta:
            logger.debug(f"Using cached {kit_type} (from {cached_download_meta.time})")
            return cached_download_meta

    core_kit_path = os.path.join(race_core.cache_path, source.asset)
    if not os.path.exists(core_kit_path):
        raise error_utils.RIB503(source.raw, "Core kit does not exist")

    logger.debug(f"Extracting core {kit_type} kit from {core_kit_path}")
    _extract_or_copy_kit(core_kit_path, cache_path, True)

    meta = KitCacheMetadata(
        source_type=source.source_type,
        source_uri=race_core.source_uri,
        auth=race_core.auth,
        time=race_core.time,
        cache_path=cache_path,
        checksum=_file_checksum(core_kit_path),
    )
    _write_cached_metadata(cache_path, meta)

    return meta


def _create_local_cache_metadata(source: KitSource) -> KitCacheMetadata:
    """
    Purpose:
        Creates the cache metadata for a local source

    Args:
        source: Kit source information

    Returns:
        Cache metadata
    """

    return KitCacheMetadata(
        source_type=source.source_type,
        source_uri=source.uri,
        auth=False,
        time=_now(),
        cache_path=source.uri,
        checksum=_dir_checksum(source.uri),
    )


def _download_remote_kit(
    kit_type: str, source: KitSource, cache: CacheStrategy, extract: bool
) -> KitCacheMetadata:
    """
    Purpose:
        Downloads (or re-uses cached) kit from a remote source

    Args:
        kit_type: Kit type
        source: RACE kit source information
        cache: Cache strategy
        extract: Extract kit archive into cache

    Returns:
        Metadata about downloaded RACE kit
    """

    if not source.uri:
        raise error_utils.RIB501(source.raw, "Remote source must specify a URI")

    cache_path = _cache_path_from_uri(source.uri)
    if _should_cache(cache, cache_on_auto=True):
        cached_download_meta = _read_cached_metadata(cache_path)
        if cached_download_meta:
            logger.debug(f"Using cached {kit_type} (from {cached_download_meta.time})")
            return cached_download_meta

    logger.debug(f"Downloading remote {kit_type} from {source.uri}")
    with tempfile.NamedTemporaryFile() as tmp_kit_file:
        (success, status_code) = network_utils.download_file(
            source.uri, tmp_kit_file.name
        )
        if not success:
            raise error_utils.RIB503(
                source.raw, f"download failed, error code {status_code}"
            )

        _extract_or_copy_kit(tmp_kit_file.name, cache_path, extract)

        meta = KitCacheMetadata(
            source_type=source.source_type,
            source_uri=source.uri,
            auth=False,
            time=_now(),
            cache_path=cache_path,
            checksum=_file_checksum(tmp_kit_file.name),
        )
        _write_cached_metadata(cache_path, meta)

    return meta


def _download_tag_kit(
    kit_type: str, source: KitSource, cache: CacheStrategy, extract: bool
) -> KitCacheMetadata:
    """
    Purpose:
        Downloads (or re-uses cached) kit from a GitHub tagged release

    Args:
        kit_type: Kit type
        source: RACE kit source information
        cache: Cache strategy
        extract: Extract kit archive into cache

    Returns:
        Metadata about downloaded RACE kit
    """

    if not source.repo or not source.tag:
        raise error_utils.RIB501(
            source.raw, "Tag source must specify the GitHub repository and tag"
        )

    if not source.org:
        source.org = github_utils.default_org()

    if not source.asset:
        source.asset = f"{source.repo}.tar.gz"

    cache_path = _cache_path(
        "gh-tag", source.org, source.repo, source.tag, source.asset
    )
    if _should_cache(cache, cache_on_auto=True):
        cached_download_meta = _read_cached_metadata(cache_path)
        if cached_download_meta:
            logger.debug(f"Using cached {kit_type} (from {cached_download_meta.time})")
            return cached_download_meta

    logger.debug(
        f"Downloading tag artifact for {kit_type} from {source.org=} "
        f"{source.repo=} {source.tag=} {source.asset=}"
    )
    with tempfile.NamedTemporaryFile() as tmp_kit_file:
        (success, status_code, auth, uri) = github_utils.download_tag_artifact(
            source.org, source.repo, source.tag, source.asset, tmp_kit_file.name
        )
        if not success:
            raise error_utils.RIB503(
                source.raw, f"download failed, error code {status_code}"
            )

        _extract_or_copy_kit(tmp_kit_file.name, cache_path, extract)

        meta = KitCacheMetadata(
            source_type=source.source_type,
            source_uri=uri,
            auth=auth,
            time=_now(),
            cache_path=cache_path,
            checksum=_file_checksum(tmp_kit_file.name),
        )
        _write_cached_metadata(cache_path, meta)

    return meta


def _download_branch_kit(
    kit_type: str, source: KitSource, cache: CacheStrategy, extract: bool
) -> KitCacheMetadata:
    """
    Purpose:
        Downloads (or re-uses cached) kit from a GitHub Actions branch

    Args:
        kit_type: Kit type
        source: RACE kit source information
        cache: Cache strategy
        extract: Extract kit archive into cache

    Returns:
        Metadata about downloaded RACE kit
    """

    if not source.repo or not source.branch:
        raise error_utils.RIB501(
            source.raw, "Branch source must specify the GitHub repository and branch"
        )

    if not source.org:
        source.org = github_utils.default_org()

    if not source.asset:
        source.asset = f"{source.repo}.tar.gz"

    # Determine the latest workflow run for the branch
    (workflow_url, download_url) = github_utils.get_latest_run_for_branch(
        source.org, source.repo, source.branch, source.asset
    )
    logger.trace(
        f"Latest workflow run for {source.branch=} {workflow_url=} {download_url=}"
    )

    # Check if we have a cached copy for the branch
    cache_path = _cache_path(
        "gh-branch", source.org, source.repo, source.branch, source.asset
    )
    cached_download_meta = _read_cached_metadata(cache_path)

    # Check if we should use the cache, auto behavior will only result in a re-download
    # if the latest workflow run for the branch has changed
    cache_on_auto = False
    if cached_download_meta and workflow_url:
        cache_on_auto = cached_download_meta.source_uri == workflow_url
        logger.trace(
            f"{cached_download_meta.source_uri=} and {workflow_url=} so {cache_on_auto=}"
        )
    if _should_cache(cache, cache_on_auto=cache_on_auto):
        if cached_download_meta:
            logger.debug(f"Using cached {kit_type} (from {cached_download_meta.time})")
            return cached_download_meta

    if not workflow_url or not download_url:
        raise error_utils.RIB503(
            source.raw, f"unable to determine latest workflow run for branch"
        )

    logger.debug(
        f"Downloading branch artifact for {kit_type} from {source.org=} "
        f"{source.repo=} {source.branch=} {source.asset=} with "
        f"{workflow_url=} {download_url=}"
    )
    with tempfile.NamedTemporaryFile() as tmp_kit_file:
        (success, status_code, auth, uri) = github_utils.download_branch_artifact(
            workflow_url, download_url, tmp_kit_file.name
        )
        if not success:
            raise error_utils.RIB503(
                source.raw, f"download failed, error code {status_code}"
            )

        _extract_or_copy_kit(tmp_kit_file.name, cache_path, extract)

        meta = KitCacheMetadata(
            source_type=source.source_type,
            source_uri=uri,
            auth=auth,
            time=_now(),
            cache_path=cache_path,
            checksum=_file_checksum(tmp_kit_file.name),
        )
        _write_cached_metadata(cache_path, meta)

    return meta


def _download_action_run_kit(
    kit_type: str, source: KitSource, cache: CacheStrategy, extract: bool
) -> KitCacheMetadata:
    """
    Purpose:
        Downloads (or re-uses cached) kit from a GitHub Actions run

    Args:
        kit_type: Kit type
        source: RACE kit source information
        cache: Cache strategy
        extract: Extract kit archive into cache

    Returns:
        Metadata about downloaded RACE kit
    """

    if not source.repo or not source.run:
        raise error_utils.RIB501(
            source.raw, "Run source must specify the GitHub repository and Actions run"
        )

    if not source.org:
        source.org = github_utils.default_org()

    if not source.asset:
        source.asset = f"{source.repo}.tar.gz"

    cache_path = _cache_path(
        "gh-run", source.org, source.repo, source.run, source.asset
    )
    if _should_cache(cache, cache_on_auto=True):
        cached_download_meta = _read_cached_metadata(cache_path)
        if cached_download_meta:
            logger.debug(f"Using cached {kit_type} (from {cached_download_meta.time})")
            return cached_download_meta

    logger.debug(
        f"Downloading GitHub actions run artifact for {kit_type} from "
        f"{source.org=} {source.repo=} {source.run=} {source.asset=}"
    )
    with tempfile.NamedTemporaryFile() as tmp_kit_file:
        (success, status_code, auth, uri) = github_utils.download_action_run_artifact(
            source.org, source.repo, source.run, source.asset, tmp_kit_file.name
        )
        if not success:
            raise error_utils.RIB503(
                source.raw, f"download failed, error code {status_code}"
            )

        _extract_or_copy_kit(tmp_kit_file.name, cache_path, extract)

        meta = KitCacheMetadata(
            source_type=source.source_type,
            source_uri=uri,
            auth=auth,
            time=_now(),
            cache_path=cache_path,
            checksum=_file_checksum(tmp_kit_file.name),
        )
        _write_cached_metadata(cache_path, meta)

    return meta


def create_kit_config(
    what: str, kit_type: KitType, source: KitSource, cache: KitCacheMetadata
) -> KitConfig:
    """
    Purpose:
        Creates a kit config object

    Args:
        what: What kit config is being created
        kit_type: Kit type
        source: Kit source
        cache: Kit cache metadata

    Returns:
        Kit config
    """

    return KitConfig(
        name=_get_kit_name(what, cache),
        kit_type=kit_type,
        source=source,
    )


def _get_kit_name(what: str, cache: KitCacheMetadata) -> str:
    """
    Purpose:
        Searches within the cached kit to determine the kit name

        The kit name is the directory underneath a platform-specific artifacts folder.

    Args:
        what: What kit is being inspected
        cache: Kit download cache metadata

    Returns:
        Kit name
    """

    artifact_re = re.compile(
        ".*artifacts/(?:linux|android)\-(?:x86_64|arm64\-v8a)\-(?:client|server)/([^/]+)/?.*$"
    )

    if os.path.isdir(cache.cache_path):
        for root, dirs, files in os.walk(cache.cache_path):
            for directory in dirs:
                full_path = os.path.join(root, directory)
                match = artifact_re.match(full_path)
                if match:
                    return match.group(1)

    elif tarfile.is_tarfile(cache.cache_path):
        with tarfile.open(cache.cache_path, "r") as tar:
            members = tar.getmembers()
            for member in members:
                match = artifact_re.match(member.name)
                if match:
                    return match.group(1)

    elif zipfile.is_zipfile(cache.cache_path):
        with zipfile.ZipFile(cache.cache_path, "r") as zip:
            entries = zip.infolist()
            for entry in entries:
                match = artifact_re.match(entry.filename)
                if match:
                    return match.group(1)

    raise error_utils.RIB505(what)


def get_channel_names(what: str, cache: KitCacheMetadata) -> List[str]:
    """
    Purpose:
        Searches within the cached kit to determine the comms channel provded by the kit

        The channel names are determined by the directories under the channels folder.

    Args:
        what: What kit is being inspected
        cache: Kit download cache metadata

    Returns:
        List of channel names
    """

    blacklist = ["race-python-utils"]

    channels_re = re.compile(r".*channels/([^/]+)/?.*$")
    channels = set()

    if os.path.isdir(cache.cache_path):
        for root, dirs, files in os.walk(cache.cache_path):
            for directory in dirs:
                full_path = os.path.join(root, directory)
                match = channels_re.match(full_path)
                if match:
                    channel = match.group(1)
                    if channel not in blacklist:
                        channels.add(channel)

    elif tarfile.is_tarfile(cache.cache_path):
        with tarfile.open(cache.cache_path, "r") as tar:
            members = tar.getmembers()
            for member in members:
                match = channels_re.match(member.name)
                if match:
                    channel = match.group(1)
                    if channel not in blacklist:
                        channels.add(channel)

    elif zipfile.is_zipfile(cache.cache_path):
        with zipfile.ZipFile(cache.cache_path, "r") as zip:
            entries = zip.infolist()
            for entry in entries:
                match = channels_re.match(entry.filename)
                if match:
                    channel = match.group(1)
                    if channel not in blacklist:
                        channels.add(channel)

    return list(channels)


def channel_plugin_has_external_services(channel_plugin_name: str, path: str) -> bool:
    """
    Purpose:
        Returns a bool representing if a channel or plugin (name and path)
        utilizes external services (confirmed by verifying the expceted
        scripts exist)

        Note: Logs an error if a folder has some but not all scripts, which

        Intended to be used for comms channels and artifact manager plugins
    Args:
        channel_plugin_name): the name of the channel for logging purposes
        path: the path to the folder that should contain the scripts
    Return:
        bool: True if all scripts exist
              False if no scripts exist
              False and logs a error if some scripts exist
    """

    required_scripts = [
        "get_status_of_external_services.sh",
        "start_external_services.sh",
        "stop_external_services.sh",
    ]

    missing_scripts = []
    for script in required_scripts:
        if not os.path.exists(f"{path}/{script}"):
            missing_scripts.append(script)

    if missing_scripts:
        if len(missing_scripts) < len(required_scripts):
            logger.error(
                "Ignoring %s, missing %s scripts, it will be ignored",
                channel_plugin_name,
                ", ".join(missing_scripts),
            )
        return False

    return True


def verify_bootstrap_channel_present(comms_channels: List[Any]) -> None:
    """
    Purpose:
        Checks that a Bootstrap channel is present

    Args:
        comms_channels: List of channel property objects
    """

    bootstrap_channel_present = False
    for comms_channel in comms_channels:
        if comms_channel.get("bootstrap", False):
            bootstrap_channel_present = True

    if not bootstrap_channel_present:
        click.secho(
            "ERROR: No Bootstrap comms channel found, all bootstrapping will fail",
            fg="red",
        )
        click.confirm("Would you like to continue?", abort=True)
