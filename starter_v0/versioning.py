from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactVersion:
    version: str
    artifact_version: str
    system_prompt_sha256: str
    tools_sha256: str


def _file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_artifact_version(version: str, system_prompt_path: str | Path, tools_path: str | Path) -> ArtifactVersion:
    system_prompt_hash = _file_sha256(system_prompt_path)
    tools_hash = _file_sha256(tools_path)
    short_hash = hashlib.sha256(f"{version}:{system_prompt_hash}:{tools_hash}".encode("utf-8")).hexdigest()[:12]
    return ArtifactVersion(
        version=version,
        artifact_version=f"{version}-{short_hash}",
        system_prompt_sha256=system_prompt_hash,
        tools_sha256=tools_hash,
    )


def artifact_version_dict(artifact_version: ArtifactVersion) -> dict[str, str]:
    return {
        "version": artifact_version.version,
        "artifact_version": artifact_version.artifact_version,
        "system_prompt_sha256": artifact_version.system_prompt_sha256,
        "tools_sha256": artifact_version.tools_sha256,
    }
