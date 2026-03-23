(async () => {
  try {
    await import('/local/photo_uploader/photo_uploader.js');
    console.debug('photo_uploader: loaded via loader');
  } catch (e) {
    // Logging helps debug resource load issues in browser console
    // Lovelace may block some logs; they still appear in devtools.
    // eslint-disable-next-line no-console
    console.error('photo_uploader loader error', e);
  }
})();
