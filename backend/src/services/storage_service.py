"""
Storage Service

Supabase Storage integration for PDF and file management.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta

from src.config.settings import settings
from src.config.supabase_client import get_async_supabase

logger = logging.getLogger(__name__)

# Bucket configuration
REPORTS_BUCKET = "reports"
DEFAULT_EXPIRY_HOURS = 24


class StorageService:
    """Service for managing file storage in Supabase."""

    def __init__(self, bucket: str = REPORTS_BUCKET):
        self.bucket = bucket

    async def upload_pdf(
        self,
        report_id: str,
        pdf_bytes: bytes,
        folder: str = "pdfs",
    ) -> Optional[str]:
        """
        Upload PDF to Supabase storage.

        Args:
            report_id: Unique report identifier
            pdf_bytes: PDF file content
            folder: Storage folder (default: "pdfs")

        Returns:
            Public URL if successful, None if failed
        """
        try:
            supabase = await get_async_supabase()
            file_path = f"{folder}/{report_id}.pdf"

            # Upload to Supabase Storage
            result = supabase.storage.from_(self.bucket).upload(
                path=file_path,
                file=pdf_bytes,
                file_options={"content-type": "application/pdf"},
            )

            if hasattr(result, "error") and result.error:
                logger.error(f"Upload failed: {result.error}")
                return None

            # Get public URL
            public_url = supabase.storage.from_(self.bucket).get_public_url(file_path)

            logger.info(f"PDF uploaded successfully: {file_path}")
            return public_url

        except Exception as e:
            logger.error(f"Failed to upload PDF: {e}")
            return None

    async def get_signed_url(
        self,
        report_id: str,
        folder: str = "pdfs",
        expires_in: int = 3600,
    ) -> Optional[str]:
        """
        Get a signed URL for secure PDF download.

        Args:
            report_id: Unique report identifier
            folder: Storage folder (default: "pdfs")
            expires_in: URL expiry in seconds (default: 1 hour)

        Returns:
            Signed URL if successful, None if failed
        """
        try:
            supabase = await get_async_supabase()
            file_path = f"{folder}/{report_id}.pdf"

            result = supabase.storage.from_(self.bucket).create_signed_url(
                path=file_path,
                expires_in=expires_in,
            )

            if isinstance(result, dict) and "signedURL" in result:
                return result["signedURL"]

            # Handle different response formats
            if hasattr(result, "signed_url"):
                return result.signed_url

            logger.warning(f"Unexpected signed URL response: {result}")
            return None

        except Exception as e:
            logger.error(f"Failed to get signed URL: {e}")
            return None

    async def delete_pdf(
        self,
        report_id: str,
        folder: str = "pdfs",
    ) -> bool:
        """
        Delete PDF from storage.

        Args:
            report_id: Unique report identifier
            folder: Storage folder (default: "pdfs")

        Returns:
            True if deleted successfully
        """
        try:
            supabase = await get_async_supabase()
            file_path = f"{folder}/{report_id}.pdf"

            result = supabase.storage.from_(self.bucket).remove([file_path])

            logger.info(f"PDF deleted: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete PDF: {e}")
            return False

    async def file_exists(
        self,
        report_id: str,
        folder: str = "pdfs",
    ) -> bool:
        """
        Check if PDF file exists in storage.

        Args:
            report_id: Unique report identifier
            folder: Storage folder (default: "pdfs")

        Returns:
            True if file exists
        """
        try:
            supabase = await get_async_supabase()
            file_path = f"{folder}/{report_id}.pdf"

            # List files to check existence
            result = supabase.storage.from_(self.bucket).list(folder)

            if result:
                filename = f"{report_id}.pdf"
                return any(f.get("name") == filename for f in result)

            return False

        except Exception as e:
            logger.error(f"Failed to check file existence: {e}")
            return False

    async def cleanup_old_files(
        self,
        days_old: int = 30,
        folder: str = "pdfs",
    ) -> int:
        """
        Clean up files older than specified days.

        Args:
            days_old: Delete files older than this many days
            folder: Storage folder to clean

        Returns:
            Number of files deleted
        """
        try:
            supabase = await get_async_supabase()
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            deleted_count = 0

            # List all files in folder
            result = supabase.storage.from_(self.bucket).list(folder)

            if not result:
                return 0

            files_to_delete = []
            for file_info in result:
                # Parse file creation date
                created_at = file_info.get("created_at")
                if created_at:
                    try:
                        file_date = datetime.fromisoformat(
                            created_at.replace("Z", "+00:00")
                        )
                        if file_date.replace(tzinfo=None) < cutoff_date:
                            files_to_delete.append(f"{folder}/{file_info['name']}")
                    except (ValueError, TypeError):
                        continue

            # Delete old files in batch
            if files_to_delete:
                supabase.storage.from_(self.bucket).remove(files_to_delete)
                deleted_count = len(files_to_delete)
                logger.info(f"Cleaned up {deleted_count} old files from {folder}")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return 0


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


# Convenience functions
async def upload_report_pdf(report_id: str, pdf_bytes: bytes) -> Optional[str]:
    """Upload a report PDF and return the public URL."""
    service = get_storage_service()
    return await service.upload_pdf(report_id, pdf_bytes)


async def get_report_download_url(report_id: str, expires_in: int = 3600) -> Optional[str]:
    """Get a signed download URL for a report PDF."""
    service = get_storage_service()
    return await service.get_signed_url(report_id, expires_in=expires_in)


async def delete_report_pdf(report_id: str) -> bool:
    """Delete a report PDF from storage."""
    service = get_storage_service()
    return await service.delete_pdf(report_id)
