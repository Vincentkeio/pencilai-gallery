# PencilAI Gallery 开源版：一键安装与使用指南

本文是一篇可以直接发到论坛/公众号/博客的「安装指导帖子」草稿。

---

## 1. 这是什么？

PencilAI Gallery 是一个基于 WordPress 的轻量画廊模板：
- 直接读取 `tg_gallery/` 目录下的图片
- Masonry 瀑布流布局 + 懒加载
- 支持「最新发布 / 随机浏览」两种浏览模式
- **开源版已移除所有会员/付费/支付相关逻辑**（不会包含任何支付地址、邮箱、回调脚本等）

> 友情提示：请确保你有权发布/分发图片素材，遵守所在地区法律与平台规则。

---

## 2. 最快安装方式（推荐：Docker 一键）

### 2.1 环境要求
- 一台 Linux 服务器（Debian/Ubuntu/CentOS 均可）
- 已安装 Docker + Docker Compose

### 2.2 一键启动

```bash
git clone <你的仓库地址> pencilai-gallery
cd pencilai-gallery/install
bash install.sh
```

安装脚本会：
- 拉起 MariaDB + WordPress 容器
- 自动安装 WordPress
- 启用主题（hamilton）
- 创建一个名为 Gallery 的页面，并设置为首页

完成后你会看到脚本输出：
- 站点地址
- 后台地址
- 管理员账号密码

---

## 3. 放图片就能用

把图片文件放进：

- `install/tg_gallery/`

支持格式：jpg/jpeg/png/webp/gif

重新刷新网页即可看到瀑布流。

> 缩略图规则：如果存在同名 `_thumb.webp`，页面会优先显示缩略图，加快加载。

---

## 4. 可选：用 Python 自动抓图/生成缩略图/建库

仓库带了可选脚本（你也可以不用）：

```bash
cd scripts
cp config.example.json config.json
# 编辑 config.json，填入你自己的 Telegram 账号参数（不要提交到 GitHub）
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 main.py once
```

脚本默认会把图片存到 `../tg_gallery/`，并在 `scripts/gallery.db` 写入元数据。

---

## 5. 常见问题

### Q1：我不想用 WordPress，可以直接用静态站吗？
可以，但本仓库提供的是 WordPress 模板版本。如果你需要纯静态版本，可以在 Issues 里提需求。

### Q2：安装后首页不是画廊？
后台设置：
- 设置 → 阅读 → 主页显示 → 静态页面 → 选择 Gallery

### Q3：我想把图片目录换位置
默认是 WordPress 根目录下的 `tg_gallery/`。
- Docker：改 `install/docker-compose.yml` 里的 volume 映射即可
- 传统部署：把目录放在站点根目录，保持路径一致

---

## 6. 安全与开源注意事项（强烈建议看）

开源仓库里**永远不要**提交这些内容：
- `wp-config.php`（数据库密码）
- 任何 `.env`/密钥/回调地址
- 生产数据库 dump
- 用户数据（uploads、订单、日志、session 等）

本开源版已默认移除上述内容。

---

如果你觉得这个项目对你有用，欢迎点个 Star ⭐️
