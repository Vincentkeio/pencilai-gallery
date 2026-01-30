# PencilAI Gallery

A clean, masonry-style WordPress image gallery that you can run in minutes.

一个极简瀑布流 WordPress 图片画廊：开箱即用、放图即用。

---

## Features | 特性

- Masonry / waterfall layout（瀑布流布局）
- Lazy loading（懒加载）
- Latest / Random sorting（最新 / 随机）
- Multi-language UI（EN / 简体 / 繁体 / 日本語）
- Direct original download（原图直链下载）
- Optional scripts: download/sync, thumbnails, sitemap（可选脚本：拉取/同步、缩略图、站点地图）

---

## What’s included | 包含什么

- WordPress **theme files only** (`wordpress/wp-content/themes/hamilton/`)
- Docker installer (`install/`)
- Optional scripts (`scripts/`)

## What’s NOT included | 不包含什么（开源安全）

- WordPress core files (wp-admin/wp-includes/...)  
- `wp-config.php`
- database dumps
- `wp-content/uploads/` or any personal images
- any membership/payment logic

---

## Directory layout | 目录约定

Images are **always** stored in repo-root:

图片目录统一为仓库根目录：

```
tg_gallery/
```

> Put images in `tg_gallery/` (not committed).  
> 图片放进去刷新即可（该目录默认不提交到 GitHub）。

---

## Quick Start (Docker, recommended) | 一键启动（Docker 推荐）

### One-liner (auto install Docker if missing) | 一行命令（自动装 Docker）
```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Vincentkeio/pencilai-gallery/main/install/bootstrap.sh)
```

### Or manual | 或手动方式
```bash
git clone https://github.com/Vincentkeio/pencilai-gallery.git
cd pencilai-gallery/install
bash install.sh
```

Open:
- `http://localhost:8080`
- or `http://<YOUR_SERVER_IP>:8080`

---

## Scripts (native, full features) | 脚本（非 Docker，功能最全）

If you want **all scripts under `scripts/` to work** (Telegram download, thumbnails, sitemap, db maintenance),
run them on the **host** (Linux) with Python venv.

如果你希望 `scripts/` 目录下脚本都能用（抓图/缩略图/站点地图/数据库维护），建议在宿主机上运行（非 Docker）。

### Setup
```bash
cd pencilai-gallery
python3 -m venv .venv
./.venv/bin/pip install -U pip
./.venv/bin/pip install -r scripts/requirements.txt
cp scripts/config.example.json scripts/config.json
# edit scripts/config.json paths.telegram... as needed
```

### Run examples
```bash
# thumbnails
./.venv/bin/python scripts/main.py thumbs

# build/update db
./.venv/bin/python scripts/sync_to_db.py

# sitemap
./.venv/bin/python scripts/generate_sitemap.py
```

> All scripts read paths from `scripts/config.json` (or env `PENCILAI_CONFIG`).  
> 所有脚本路径统一由 `scripts/config.json` 控制（或环境变量 `PENCILAI_CONFIG`）。

---

## Manual install (existing WordPress) | 已有 WordPress 的手动安装

Copy theme files:

```text
wordpress/wp-content/themes/hamilton/
```

to your site:

```text
wp-content/themes/hamilton/
```

Then create a page and select template:
- `PencilAI Gallery (Open Source)`

---

## License

GPL-2.0-or-later
