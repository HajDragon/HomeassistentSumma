(() => {
  class PhotoUploader extends HTMLElement {
    set hass(hass) {
      this._hass = hass;
      if (!this._initialized && this._config) this._init();
    }

    setConfig(config) {
      this._config = config || {};
      if (!this._initialized && (this._hass || true)) this._init();
    }

    getCardSize() {
      return 3;
    }

    _init() {
      this._initialized = true;
      this.innerHTML = `
        <style>
          .photo-uploader { display:flex; flex-direction:column; gap:8px; }
          .photo-preview { max-width:100%; max-height:200px; object-fit:contain; }
          .photo-uploader button { padding:6px 10px; }
        </style>
        <div class="photo-uploader">
          <input type="file" accept="image/*" id="fileinput">
          <img id="preview" class="photo-preview" style="display:none"/>
          <div>
            <button id="upload">Upload</button>
            <span id="status" style="margin-left:8px"></span>
          </div>
        </div>
      `;
      const fileInput = this.querySelector('#fileinput');
      const uploadBtn = this.querySelector('#upload');
      if (fileInput) fileInput.addEventListener('change', e => this._onFileSelected(e.target.files));
      if (uploadBtn) uploadBtn.addEventListener('click', () => this._upload());
    }

    _onFileSelected(files) {
      this._file = files && files[0];
      const preview = this.querySelector('#preview');
      const status = this.querySelector('#status');
      status.textContent = '';
      if (!this._file) { preview.style.display='none'; return; }
      const reader = new FileReader();
      reader.onload = e => {
        preview.src = e.target.result;
        preview.style.display = '';
        this._dataUrl = e.target.result;
      };
      reader.readAsDataURL(this._file);
    }

    async _upload() {
      const status = this.querySelector('#status');
      if (!this._file || !this._dataUrl) { status.textContent = 'No file selected'; return; }
      status.textContent = 'Uploading...';
      const content = this._dataUrl.split(',')[1];
      try {
        await this._hass.callService('photo_scanner', 'upload', { filename: this._file.name, content, overwrite: true });
        status.textContent = 'Upload complete';
      } catch (err) {
        status.textContent = 'Upload failed';
        console.error('Photo upload error', err);
      }
    }
  }

  // Avoid redefining the element if it's already registered (prevents DOMException)
  if (!customElements.get('photo-uploader')) {
    customElements.define('photo-uploader', PhotoUploader);
  } else {
    // If an older registration exists, patch missing methods so Lovelace can call them
    const Ex = customElements.get('photo-uploader');
    const srcProto = PhotoUploader.prototype;
    if (!Ex.prototype.setConfig && srcProto.setConfig) Ex.prototype.setConfig = srcProto.setConfig;
    if (!Ex.prototype.getCardSize && srcProto.getCardSize) Ex.prototype.getCardSize = srcProto.getCardSize;
    if (!Ex.prototype._init && srcProto._init) Ex.prototype._init = srcProto._init;
    if (!Ex.prototype._onFileSelected && srcProto._onFileSelected) Ex.prototype._onFileSelected = srcProto._onFileSelected;
    if (!Ex.prototype._upload && srcProto._upload) Ex.prototype._upload = srcProto._upload;
  }
  window.customCards = window.customCards || [];
  window.customCards.push({
    type: 'photo-uploader',
    name: 'Photo Uploader',
    preview: true,
    description: 'Upload photos to /local/photos for the Photo Scanner.',
  });
})();
