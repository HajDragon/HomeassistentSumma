"""Photo Scanner integration.

This custom integration provides a single service:
  photo_scanner.scan

Which scans the HA config/www/photos directory for supported image files
and updates an `input_select.available_photos` helper with the results.
"""

from __future__ import annotations

from pathlib import Path
from homeassistant.core import HomeAssistant, ServiceCall

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

    return True