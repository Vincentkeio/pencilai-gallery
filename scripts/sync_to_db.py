import os
import sqlite3
from datetime import datetime

# 配置与 main.py 保持一致
db_path = '/www/wwwroot/pencilai.top/scripts/gallery.db'
gallery_dir = '/www/wwwroot/pencilai.top/tg_gallery/'

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