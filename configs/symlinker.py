"""Config deployment - symlink strategy with safe, idempotent behavior."""
import os
import shutil
from enum import Enum
from pathlib import Path
from datetime import datetime

from bootstrap.logging import get_logger
from bootstrap.models import DeploymentResult

logger = get_logger("bootstrap.configs")


class TargetDisposition(Enum):
    """How the deployment target relates to the desired source."""
    ABSENT = "absent"
    CORRECT_SYMLINK = "correct_symlink"
    WRONG_SYMLINK = "wrong_symlink"
    IDENTICAL_FILE = "identical_file"
    DIFFERENT_FILE = "different_file"
    NON_FILE = "non_file"


class Symlinker:
    """Handles symlink-based config deployment."""

    def __init__(self, backup_dir: Path | None = None):
        self.backup_dir = backup_dir or Path.home() / ".config" / "dotfiles-backup"

    @staticmethod
    def _max_compare_bytes() -> int:
        return 2_000_000

    def classify_target(self, source: Path, target: Path) -> TargetDisposition:
        """Classify an existing target path for deployment decisions."""
        if not target.exists() and not target.is_symlink():
            return TargetDisposition.ABSENT

        if target.is_symlink():
            try:
                if target.resolve() == source.resolve():
                    return TargetDisposition.CORRECT_SYMLINK
            except OSError:
                return TargetDisposition.WRONG_SYMLINK
            return TargetDisposition.WRONG_SYMLINK

        if target.is_file():
            try:
                if self._files_identical(source, target):
                    return TargetDisposition.IDENTICAL_FILE
            except OSError:
                return TargetDisposition.DIFFERENT_FILE
            return TargetDisposition.DIFFERENT_FILE

        return TargetDisposition.NON_FILE

    def _files_identical(self, a: Path, b: Path) -> bool:
        if not a.is_file() or not b.is_file():
            return False
        sa = a.stat()
        sb = b.stat()
        if sa.st_size != sb.st_size:
            return False
        if sa.st_size > self._max_compare_bytes():
            return False
        return a.read_bytes() == b.read_bytes()

    def deploy(
        self,
        source: Path,
        target: Path,
        dry_run: bool = False,
        replace_conflicts: bool = True,
    ) -> DeploymentResult:
        """
        Deploy a config file via symlink.

        replace_conflicts:
            True  -> backup (if needed) and replace mismatched targets.
            False -> leave mismatched targets untouched.
        """
        if not source.exists():
            return DeploymentResult(
                success=False,
                action="skip",
                target=target,
                message=f"Source file does not exist: {source}",
                error="Source not found",
            )

        disposition = self.classify_target(source, target)

        if disposition == TargetDisposition.CORRECT_SYMLINK:
            return DeploymentResult(
                success=True,
                action="skip",
                target=target,
                message="Already symlinked to the correct source",
            )

        if disposition == TargetDisposition.IDENTICAL_FILE:
            return DeploymentResult(
                success=True,
                action="skip",
                target=target,
                message="Existing file matches source content; leaving in place",
            )

        if disposition in (TargetDisposition.WRONG_SYMLINK, TargetDisposition.DIFFERENT_FILE):
            if not replace_conflicts:
                return DeploymentResult(
                    success=True,
                    action="skip",
                    target=target,
                    message="Target exists and differs; skipping due to policy",
                )

        if disposition == TargetDisposition.NON_FILE:
            return DeploymentResult(
                success=False,
                action="skip",
                target=target,
                message=f"Target exists but is not a regular file/symlink: {target}",
                error="unsupported target type",
            )

        backup_path = None
        if disposition in (TargetDisposition.WRONG_SYMLINK, TargetDisposition.DIFFERENT_FILE):
            if dry_run:
                logger.info(f"  [DRY RUN] Would backup and replace: {target}")
            else:
                backup_path = self._create_backup(target)
                logger.info(f"  Backed up existing path to: {backup_path}")

        if dry_run:
            return DeploymentResult(
                success=True,
                action="symlink",
                target=target,
                message=f"[DRY RUN] Would create symlink: {target} -> {source}",
                backup_path=backup_path,
            )

        target.parent.mkdir(parents=True, exist_ok=True)

        if target.exists() or target.is_symlink():
            target.unlink()

        try:
            os.symlink(source, target)
            return DeploymentResult(
                success=True,
                action="symlink",
                target=target,
                message=f"Created symlink: {target} -> {source}",
                backup_path=backup_path,
            )
        except OSError as e:
            return DeploymentResult(
                success=False,
                action="symlink",
                target=target,
                message=f"Failed to create symlink: {e}",
                error=str(e),
            )

    def _create_backup(self, target: Path) -> Path:
        """Create a timestamped backup of an existing file or symlink."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name

        if target.is_symlink():
            backup_path.write_text(os.readlink(target))
            return backup_path

        shutil.copy2(target, backup_path)
        return backup_path
