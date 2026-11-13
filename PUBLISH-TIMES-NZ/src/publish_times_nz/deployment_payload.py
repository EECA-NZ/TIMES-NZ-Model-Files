"""Create the small, explicit rsconnect deployment payload."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import uuid

from publish_times_nz.release_bundle import load_bundle


def prepare_deployment_payload(publish_root: Path, release_name: str = "v308") -> Path:
    """Rebuild ``deployment_payload`` with the app and one selected release."""
    release_path = publish_root / "releases" / release_name
    env_path = publish_root / ".env"
    if not env_path.is_file():
        raise ValueError(f"Missing deployment environment file: {env_path}")
    load_bundle(release_path)

    deploy_path = publish_root / "deployment_payload"
    staging_path = publish_root / f".deployment_payload.{uuid.uuid4().hex}.staging"
    try:
        _copy(publish_root / "app.py", staging_path / "app.py")
        _write_requirements(publish_root, staging_path / "requirements.txt")
        _copy(env_path, staging_path / ".env")
        _copy(publish_root / "src", staging_path / "src")
        _copy(publish_root / "assets", staging_path / "assets")
        _copy(publish_root / "www", staging_path / "www")
        _copy(release_path, staging_path / "releases" / release_name)
        load_bundle(staging_path / "releases" / release_name)

        shutil.rmtree(deploy_path, ignore_errors=True)
        staging_path.rename(deploy_path)
    except Exception:
        shutil.rmtree(staging_path, ignore_errors=True)
        raise
    return deploy_path


def _write_requirements(publish_root: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "uv",
            "export",
            "--locked",
            "--package",
            "publish-times-nz",
            "--no-dev",
            "--no-emit-workspace",
            "--no-hashes",
            "-o",
            str(destination),
        ],
        check=True,
        cwd=publish_root.parent,
        stdout=subprocess.DEVNULL,
    )


def _copy(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__"))
    elif source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    else:
        raise ValueError(f"Missing deployment input: {source}")
