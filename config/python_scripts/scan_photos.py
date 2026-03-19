# Scan www/photos and update the input_select helper with available image files.
# This runs in Home Assistant's python_script environment.
# See: https://www.home-assistant.io/integrations/python_script/

import os

# Supported image extensions
SUPPORTED = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

photos_dir = hass.config.path("www", "photos")

# Ensure directory exists (create if missing)
if not os.path.isdir(photos_dir):
    try:
        os.makedirs(photos_dir, exist_ok=True)
    except Exception as e:
        hass.services.call(
            "persistent_notification",
            "create",
            {
                "title": "Scan Photos - Error",
                "message": f"Could not create directory {photos_dir}: {e}",
                "notification_id": "scan_photos_error",
            },
        )
        files = []
    else:
        files = []
else:
    files = sorted(
        f for f in os.listdir(photos_dir)
        if os.path.isfile(os.path.join(photos_dir, f))
        and os.path.splitext(f)[1].lower() in SUPPORTED
    )

if not files:
    options = ["(geen foto's gevonden)"]
else:
    options = files

# Update input_select helper
hass.services.call(
    "input_select",
    "set_options",
    {
        "entity_id": "input_select.available_photos",
        "options": options,
    },
)

# Debug notification
message = (
    f"Directory: {photos_dir}\nFound {len(files)} image(s): {files}"
    if files else
    f"Directory: {photos_dir}\nNo photos found."
)
hass.services.call(
    "persistent_notification",
    "create",
    {
        "title": "Scan Photos",
        "message": message,
        "notification_id": "scan_photos_notification",
    },
)
