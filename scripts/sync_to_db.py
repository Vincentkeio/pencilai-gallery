import os
import json
import sqlite3
from datetime import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(BASE_DIR, 'config.json')

def _load_config_paths():
    # Use config.json if present; fallback to config.example.json for path defaults
    cfg_path = os.environ.get('PENCILAI_CONFIG', DEFAULT_CONFIG)
    if not os.path.exists(cfg_path):
        cfg_path = os.path.join(BASE_DIR, 'config.example.json')
    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    paths = cfg.get('paths', {}) if isinstance(cfg, dict) else {}
    db_path = paths.get('db_path', './gallery.db')
    tg_dir = paths.get('tg_gallery_dir', '../tg_gallery')
    # resolve relative paths against scripts/ directory
    if not os.path.isabs(db_path):
        db_path = os.path.abspath(os.path.join(BASE_DIR, db_path))
    if not os.path.isabs(tg_dir):
        tg_dir = os.path.abspath(os.path.join(BASE_DIR, tg_dir))
    return db_path, tg_dir


# resolved paths
db_path, gallery_dir = _load_config_paths()


# 配置与 main.py 保持一致
def sync_existing_files():
    # 初始化数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS images 
        (id TEXT PRIMARY KEY, channel TEXT, timestamp INTEGER, file_name TEXT)''')

    # 只扫描原图（不扫描 thumb 缩略图）
    files = [f for f in os.listdir(gallery_dir) if f.endswith('.jpg') and not f.endswith('_thumb.webp')]
    print(f"📡 发现本地 {len(files)} 张存量图片，正在补录进数据库...")

    count = 0
    for f in files:
        try:
            # 文件名格式：photo_2024-12-25_12-00-00_ID.jpg
            parts = f.replace('.jpg', '').split('_')
            if len(parts) >= 4:
                # 解析日期和时间
                date_str = f"{parts[1]} {parts[2].replace('-', ':')}"
                ts = int(datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').timestamp())
                msg_id = parts[3]
                
                # 写入数据库，标记频道为 "Legacy" (存量图无法追溯原始频道)
                cursor.execute("INSERT OR IGNORE INTO images VALUES (?, ?, ?, ?)", 
                               (msg_id, "Legacy", ts, f))
                count += 1
        except Exception as e:
            continue
    
    conn.commit()
    conn.close()
    print(f"✅ 成功补录 {count} 条数据。现在你可以修改前端 PHP 使用 SQL 排序了！")

if __name__ == "__main__":
    sync_existing_files()