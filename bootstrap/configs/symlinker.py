"""Config deployment - symlink strategy."""
import os
import shutil
from pathlib import Path
from datetime import datetime

from bootstrap.logging import get_logger
from bootstrap.models import DeploymentStrategy, DeploymentResult

logger = get_logger("bootstrap.configs")


class Symlinker:
    """Handles symlink-based config deployment."""
    
    def __init__(self, backup_dir: Path | None = None):
        self.backup_dir = backup_dir or Path.home() / ".config" / "dotfiles-backup"
    
    def deploy(self, source: Path, target: Path, dry_run: bool = False) -> DeploymentResult:
        """Deploy a config file via symlink."""
        
        # Check if source exists
        if not source.exists():
            return DeploymentResult(
                success=False,
                action="symlink",
                target=target,
                message=f"Source file does not exist: {source}",
                error="Source not found"
            )
        
        # Check if target already exists or is a symlink
        backup_path = None
        
        if target.exists() or target.is_symlink():
            if dry_run:
                logger.info(f"  [DRY RUN] Would backup and replace: {target}")
            else:
                # Create backup
                backup_path = self._create_backup(target)
                logger.info(f"  Backed up existing file to: {backup_path}")
        
        if dry_run:
            return DeploymentResult(
                success=True,
                action="symlink",
                target=target,
                message=f"[DRY RUN] Would create symlink: {target} -> {source}"
            )
        
        # Create parent directories if needed
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Remove existing file/symlink
        if target.exists() or target.is_symlink():
            target.unlink()
        
        # Create symlink
        try:
            os.symlink(source, target)
            return DeploymentResult(
                success=True,
                action="symlink",
                target=target,
                message=f"Created symlink: {target} -> {source}",
                backup_path=backup_path
            )
        except Exception as e:
            return DeploymentResult(
                success=False,
                action="symlink",
                target=target,
                message=f"Failed to create symlink: {e}",
                error=str(e)
            )
    
    def _create_backup(self, target: Path) -> Path:
        """Create a timestamped backup of existing file."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(target, backup_path)
        return backup_path
