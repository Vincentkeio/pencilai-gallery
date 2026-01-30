特点：

极简瀑布流

原图直链下载

多语言

无会员、无支付、无后台配置

Docker 一键跑起来

支持自动生成缩略图 + 图片数据库

GitHub：
https://github.com/Vincentkeio/pencilai-gallery

一键安装（推荐）

要求：

装好 Docker

装好 Docker Compose

执行：

git clone https://github.com/Vincentkeio/pencilai-gallery.git
cd pencilai-gallery/install
bash install.sh


浏览器打开：

http://localhost:8080

添加图片

把图片丢进：

install/tg_gallery/


刷新页面即可。

可选：生成缩略图（强烈推荐）

进入脚本目录：

cd scripts
python generate_thumbs.py


会自动为所有图片生成 _thumb.webp。

可选：建立图片数据库（大量图片时更快）
python build_gallery_db.py


这样 WordPress 不需要扫描文件夹，性能非常好。

已有 WordPress 的人

直接复制主题：

wordpress/wp-content/themes/hamilton


到你的站点即可。

为什么要用这个？

因为现有 WordPress 图库插件都太重、太丑、太复杂。

这个就是纯展示 + 下载，干净到极致。

如果你需要大规模图片站，这个真的非常合适。
