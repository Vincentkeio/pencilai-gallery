# PencilAI Gallery

> A clean, masonry-style WordPress image gallery powered by Docker.  
> Zero membership. Zero payment. Zero configuration. Just drop images and run.

> 一个极简、瀑布流风格的 WordPress 图片画廊。  
> 无会员、无支付、无配置，放图即用。

---

## ✨ Features | 特性

- Masonry waterfall layout（瀑布流布局）
- Lazy loading images（图片懒加载）
- Multi-language UI（多语言：EN / 简 / 繁 / JP）
- Random / Latest sorting（随机 / 最新排序）
- File size display + direct download（显示大小 + 原图下载）
- Docker one-click install（Docker 一键安装）
- Optional image crawler & thumbnail generator（可选抓图/缩略图脚本）

---

## ❗ Important | 重要说明

This repository **does NOT include**:

- WordPress core
- wp-config.php
- uploads / images
- any database
- any payment / membership code

Docker installation will automatically pull the official WordPress image.

本仓库 **不包含**：

- WordPress 核心
- 任何数据库 / 图片
- 任何支付或会员逻辑

Docker 安装会自动拉取官方 WordPress 镜像。

---

## 🚀 Quick Start (Docker) | 一键启动

Requirements:

- Docker
- Docker Compose

```bash
git clone https://github.com/Vincentkeio/pencilai-gallery.git
cd pencilai-gallery/install
bash install.sh
