"""Photo Scanner integration.

This custom integration provides a single service:
  photo_scanner.scan

Which scans the HA config/www/photos directory for supported image files
and updates an `input_select.available_photos` helper with the results.
"""

from __future__ import annotations

from pathlib import Path
from homeassistant.core import HomeAssistant, ServiceCall
import base64
import os
import logging

DOMAIN = "photo_scanner"
SERVICE_SCAN = "scan"

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
INPUT_SELECT = "input_select.available_photos"


def _format_files(path: Path) -> list[str]:
    """Return sorted list of supported image filenames in a directory."""
    try:
        return sorted(
            f.name
            for f in path.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        )
    except FileNotFoundError:
        return []


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Photo Scanner service."""

    async def async_scan(call: ServiceCall) -> None:
        # Convert the string path to a modern Path object
        photos_dir = Path(hass.config.path("www", "photos"))
        
        # Run the blocking file system read in an executor thread 
        # so it doesn't block the Home Assistant event loop
        files = await hass.async_add_executor_job(_format_files, photos_dir)

        if not files:
            options = ["(geen foto's gevonden)"]
        else:
            options = files

        await hass.services.async_call(
            "input_select",
            "set_options",
            {"entity_id": INPUT_SELECT, "options": options},
            blocking=True,
        )

        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Scan Photos (photo_scanner)",
                "message": f"Directory: {photos_dir}\nFound {len(files)} image(s): {files}",
                "notification_id": "scan_photos_notification",
            },
            blocking=True,
        )

    hass.services.async_register(DOMAIN, SERVICE_SCAN, async_scan)

    async def async_upload(call: ServiceCall) -> None:
        """Handle uploaded file content (base64) and save to www/photos.

        Expected service data:
          - filename: the target filename (string)
          - content: base64-encoded file data (string, no data: prefix)
          - overwrite: optional bool (default True)
        """
        filename = call.data.get("filename")
        content = call.data.get("content")
        overwrite = call.data.get("overwrite", True)

        _LOGGER = logging.getLogger(__name__)

        if not filename or not content:
            _LOGGER.error("photo_scanner.upload called without filename/content")
            return

        # Sanitize filename to avoid directory traversal
        filename = os.path.basename(filename)

        photos_dir = Path(hass.config.path("www", "photos"))
        try:
            photos_dir.mkdir(parents=True, exist_ok=True)
        except Exception as err:
            _LOGGER.exception("Could not ensure photos directory: %s", err)
            return

        target = photos_dir / filename
        if target.exists() and not overwrite:
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Photo Upload",
                    "message": f"File exists and overwrite disabled: {filename}",
                    "notification_id": "photo_upload_exists",
                },
                blocking=True,
            )
            return

        # Decode base64 and write file in executor
        try:
            raw = base64.b64decode(content)
        except Exception as err:
            _LOGGER.exception("Failed to decode uploaded content: %s", err)
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "Photo Upload",
                    "message": f"Failed to decode uploaded file {filename}",
                    "notification_id": "photo_upload_decode_error",
                },
                blocking=True,
            )
            return

        def _write_bytes(path: str, data: bytes) -> None:
            with open(path, "wb") as f:
                f.write(data)

        await hass.async_add_executor_job(_write_bytes, str(target), raw)

        # Trigger a scan to update the input_select options immediately
        try:
            await hass.services.async_call(DOMAIN, SERVICE_SCAN, {}, blocking=True)
        except Exception:
            # non-fatal if scan fails
            pass

        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Photo Upload",
                "message": f"Saved uploaded photo: {filename}",
                "notification_id": "photo_upload_success",
            },
            blocking=True,
        )

    hass.services.async_register(DOMAIN, "upload", async_upload)

    return True