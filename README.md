### ACTIVOS POR AREA

<p align="center">
    This project was developed to register and manage assets by their corresponding area. It allows users to store detailed asset information, including name, description, properties, and an associated image captured from camera, clipboard, or local file.
    The system organizes assets by area to improve management and accessibility.
</p>

### TECHNOLOGIES USED
- Python.
    - NiceGUI.
- PocketBase (Backend / API)
- OpenCV (cv2).

### MAIN FEATURES
#### NEW ASSET
This section allows users to register new assets:
- Image capture via:
    - Live camera (OpenCV).
    - Clipboard.
    - Local file upload.
- Data entry:
    - Asset name.
    - Assigned area.
    - Description.
    - Dynamic properties (key / value).
- Storage in PocketBase database.
<p align="center">
  <img width="1000" height="562" alt="image" src="https://github.com/user-attachments/assets/2d9d3a92-a91f-4982-8c96-4837177da74a" />
</p>

#### ASSETS
This section displays all registered assets:
- Grouped by area.
- Image preview per asset.
- Description and properties.
- Card-based interactive UI.
- Image zoom view.
<p align="center">
  <img width="1000" height="562" alt="image" src="https://github.com/user-attachments/assets/aea1a3c7-ca8b-47ca-8f3c-879b8c07800c" />
</p>
