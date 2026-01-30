# 安装与使用（Docker 推荐）

## Docker 一键安装（自动检测/安装 Docker）

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/Vincentkeio/pencilai-gallery/main/install/bootstrap.sh)
```

完成后访问：
- http://<服务器IP>:8080
- 后台：http://<服务器IP>:8080/wp-admin

图片目录（宿主机）：
- 仓库根目录 `tg_gallery/`（放图刷新即可）。Docker 会把它挂载到容器的 /var/www/html/tg_gallery

## 非 Docker 安装（脚本功能最全）

> 如果你希望 scripts 里的所有脚本都能直接运行（抓图/缩略图/站点地图/DB 维护），建议用该方式。

```bash
git clone https://github.com/Vincentkeio/pencilai-gallery.git
cd pencilai-gallery/install
sudo bash native_install.sh DOMAIN=your.domain SITE_URL=http://your.domain
```

脚本环境：
- 仓库根目录会创建 `.venv`
- 复制 `scripts/config.example.json -> scripts/config.json` 后即可按需配置
