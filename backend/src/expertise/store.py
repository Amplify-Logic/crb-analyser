"""
ExpertiseStore - Persistent storage for agent expertise.

Handles reading and writing expertise files with:
- Atomic writes (prevents corruption)
- File locking (prevents race conditions)
- Pydantic validation (ensures data integrity)
"""

import json
import os
import tempfile
import fcntl
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Type, TypeVar

from pydantic import BaseModel

from .schemas import (
    IndustryExpertise,
    VendorExpertise,
    ExecutionExpertise,
    AnalysisRecord,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Base path for expertise data
EXPERTISE_DIR = Path(__file__).parent / "data"


class ExpertiseStore:
    """
    Manages persistence of expertise files.

    Uses atomic writes and file locking to ensure data integrity
    even with concurrent analysis runs.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or EXPERTISE_DIR
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        (self.base_dir / "industries").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "records").mkdir(parents=True, exist_ok=True)

    def _get_industry_path(self, industry: str) -> Path:
        """Get path for industry expertise file."""
        safe_name = industry.lower().replace(" ", "-").replace("/", "-")
        return self.base_dir / "industries" / f"{safe_name}.json"

    def _get_vendor_path(self) -> Path:
        """Get path for vendor expertise file."""
        return self.base_dir / "vendors.json"

    def _get_execution_path(self) -> Path:
        """Get path for execution expertise file."""
        return self.base_dir / "execution.json"

    def _get_record_path(self, audit_id: str) -> Path:
        """Get path for an analysis record."""
        return self.base_dir / "records" / f"{audit_id}.json"

    def _read_json(self, path: Path, model_class: Type[T]) -> Optional[T]:
        """
        Read and validate a JSON file into a Pydantic model.
        Returns None if file doesn't exist.
        """
        if not path.exists():
            return None

        try:
            with open(path, "r") as f:
                # Acquire shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    return model_class.model_validate(data)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error reading {path}: {e}")
            return None

    def _write_json(self, path: Path, model: BaseModel) -> bool:
        """
        Write a Pydantic model to JSON with atomic write.

        Uses write-to-temp-then-rename pattern to prevent corruption.
        """
        try:
            # Serialize to JSON
            data = model.model_dump(mode="json")

            # Write to temporary file first
            dir_path = path.parent
            fd, temp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp")

            try:
                with os.fdopen(fd, "w") as f:
                    # Acquire exclusive lock
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    try:
                        json.dump(data, f, indent=2, default=str)
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                # Atomic rename
                os.rename(temp_path, path)
                return True

            except Exception:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise

        except Exception as e:
            logger.error(f"Error writing {path}: {e}")
            return False

    # =========================================================================
    # Industry Expertise
    # =========================================================================

    def get_industry_expertise(self, industry: str) -> IndustryExpertise:
        """
        Get expertise for an industry.
        Returns empty expertise if none exists yet.
        """
        path = self._get_industry_path(industry)
        expertise = self._read_json(path, IndustryExpertise)

        if expertise is None:
            # Create new expertise for this industry
            expertise = IndustryExpertise(industry=industry)
            logger.info(f"Created new expertise file for industry: {industry}")

        return expertise

    def save_industry_expertise(self, expertise: IndustryExpertise) -> bool:
        """Save industry expertise."""
        expertise.last_updated = datetime.utcnow()
        expertise.update_confidence()
        path = self._get_industry_path(expertise.industry)
        success = self._write_json(path, expertise)
        if success:
            logger.info(
                f"Saved expertise for {expertise.industry} "
                f"(analyses: {expertise.total_analyses}, confidence: {expertise.confidence})"
            )
        return success

    def list_industries_with_expertise(self) -> list[str]:
        """List all industries that have expertise files."""
        industries_dir = self.base_dir / "industries"
        if not industries_dir.exists():
            return []

        return [
            f.stem for f in industries_dir.glob("*.json")
            if not f.name.startswith("_")
        ]

    # =========================================================================
    # Vendor Expertise
    # =========================================================================

    def get_vendor_expertise(self) -> VendorExpertise:
        """Get vendor expertise."""
        path = self._get_vendor_path()
        expertise = self._read_json(path, VendorExpertise)

        if expertise is None:
            expertise = VendorExpertise()

        return expertise

    def save_vendor_expertise(self, expertise: VendorExpertise) -> bool:
        """Save vendor expertise."""
        expertise.last_updated = datetime.utcnow()
        path = self._get_vendor_path()
        return self._write_json(path, expertise)

    # =========================================================================
    # Execution Expertise
    # =========================================================================

    def get_execution_expertise(self) -> ExecutionExpertise:
        """Get execution expertise."""
        path = self._get_execution_path()
        expertise = self._read_json(path, ExecutionExpertise)

        if expertise is None:
            expertise = ExecutionExpertise()

        return expertise

    def save_execution_expertise(self, expertise: ExecutionExpertise) -> bool:
        """Save execution expertise."""
        expertise.last_updated = datetime.utcnow()
        path = self._get_execution_path()
        return self._write_json(path, expertise)

    # =========================================================================
    # Analysis Records
    # =========================================================================

    def save_analysis_record(self, record: AnalysisRecord) -> bool:
        """Save an analysis record for later distillation."""
        path = self._get_record_path(record.audit_id)
        return self._write_json(path, record)

    def get_analysis_record(self, audit_id: str) -> Optional[AnalysisRecord]:
        """Get a specific analysis record."""
        path = self._get_record_path(audit_id)
        return self._read_json(path, AnalysisRecord)

    def get_recent_records(self, limit: int = 50) -> list[AnalysisRecord]:
        """Get recent analysis records for batch learning."""
        records_dir = self.base_dir / "records"
        if not records_dir.exists():
            return []

        # Get all record files sorted by modification time
        record_files = sorted(
            records_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:limit]

        records = []
        for path in record_files:
            record = self._read_json(path, AnalysisRecord)
            if record:
                records.append(record)

        return records

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    def get_all_expertise_context(self, industry: str) -> dict:
        """
        Get all relevant expertise for an analysis.
        This is what gets injected into the agent's context.
        """
        return {
            "industry_expertise": self.get_industry_expertise(industry).model_dump(),
            "vendor_expertise": self.get_vendor_expertise().model_dump(),
            "execution_expertise": self.get_execution_expertise().model_dump(),
        }


# Singleton instance
_store: Optional[ExpertiseStore] = None


def get_expertise_store() -> ExpertiseStore:
    """Get the singleton expertise store instance."""
    global _store
    if _store is None:
        _store = ExpertiseStore()
    return _store
