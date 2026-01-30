# PencilAI Gallery (Open Source Edition)

This repository is an **open-source export** of a PencilAI-style gallery site.

It contains:
- A WordPress theme template (`page-gallery.php`) that renders a Masonry-style gallery from a `tg_gallery/` folder.
- Optional Python scripts to ingest images and generate thumbnails + SQLite metadata.
- A Docker-based one-click installer.

> Note: This export intentionally **removes membership/paywall logic and any payment information**.

## Quick start (Docker)

```bash
cd install
bash install.sh
```

Then open the printed URL and upload some images into `install/tg_gallery/`.

## Python ingestion (optional)

```bash
cd scripts
cp config.example.json config.json
# edit config.json with your own Telegram credentials
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 main.py once
```

## What is NOT included

- No `wp-config.php` / secrets
- No production database dumps
- No `wp-content/uploads` media
- No payment addresses / PayPal emails
- No Google Indexing service account key

## License

Recommended: `GPL-2.0-or-later` for WordPress theme code.
