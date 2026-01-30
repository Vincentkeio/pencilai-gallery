import os
import sqlite3
import time

# ================= 配置区域 =================
base_dir = '/www/wwwroot/pencilai.top/scripts'
db_path = os.path.join(base_dir, 'gallery.db')
gallery_dir = '/www/wwwroot/pencilai.top/tg_gallery'
# ===========================================

def init_and_migrate_db():
    """【整合功能】初始化数据库索引并补齐缺失的入库时间"""
    if not os.path.exists(db_path): return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print("🚀 启动数据库维护：初始化索引与补齐时间...")

    # 1. 结构维护：确保 captured_at 字段存在
    try:
        cursor.execute("ALTER TABLE images ADD COLUMN captured_at INTEGER")
        print("✅ 成功检查/添加 captured_at 字段。")
    except sqlite3.OperationalError:
        pass

    # 2. 数据维护：补齐历史记录的时间戳权重
    cursor.execute("SELECT COUNT(*) FROM images WHERE captured_at IS NULL")
    missing_count = cursor.fetchone()[0]
    if missing_count > 0:
        current_now = int(time.time())
        cursor.execute("UPDATE images SET captured_at = ? WHERE captured_at IS NULL", (current_now,))
        print(f"📊 已为 {missing_count} 条历史记录补齐入库时间。")

    # 3. 性能优化：建立复合高速索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sort_flow ON images (captured_at, timestamp)")
    print("⚡ 复合索引 idx_sort_flow 已就绪。")
    
    conn.commit()
    conn.close()

def deep_clean_and_limit():
    """物理清理核心逻辑：原图为本，不删无缩略图的原图"""
    if not os.path.exists(db_path): return
    
    # 🌟 先执行数据库初始化维护
    init_and_migrate_db()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔍 启动物理清理：遵循“原图至上”原则...")
    orphan_thumb = 0    # 已删除的孤儿缩略图
    dead_db_count = 0   # 数据库死链记录
    
    all_files = set(os.listdir(gallery_dir))
    
    # --- 1. 双向孤儿检查 (已改为只清理孤儿缩略图) ---
    for f in list(all_files):
        f_path = os.path.join(gallery_dir, f)
        
        # 情况 A: 清理孤儿缩略图
        if f.endswith('_thumb.webp'):
            original_jpg = f.replace('_thumb.webp', '.jpg')
            if original_jpg not in all_files:
                try:
                    os.remove(f_path)
                    orphan_thumb += 1
                except: pass
        
        # 情况 B: 原图无缩略图
        # 🌟 逻辑已反转：只要是 .jpg 且文件存在，此处不做任何操作，确保原图安全。

    # --- 2. 数据库死链清理 (物理原图已失踪的记录) ---
    cursor.execute("SELECT file_name FROM images")
    db_records = cursor.fetchall()
    for (fname,) in db_records:
        if fname not in all_files:
            cursor.execute("DELETE FROM images WHERE file_name = ?", (fname,))
            dead_db_count += 1

    # --- 3. 1-4-7 采样规则清理 (保持不变) ---
    current_files = [f for f in os.listdir(gallery_dir) if f.endswith('.jpg') and not f.endswith('_thumb.webp')]
    groups = {}
    for f in current_files:
        try:
            parts = f.split('_')
            if len(parts) < 6: continue
            group_id = parts[4]
            if group_id.startswith('S'): continue
            group_key = f"{parts[1]}_{parts[2]}_{parts[3]}_{group_id}"
            if group_key not in groups: groups[group_key] = []
            groups[group_key].append(f)
        except: continue

    redundant_deleted = 0
    for group_key, file_list in groups.items():
        if len(file_list) <= 4: continue
        file_list.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
        to_keep = [file_list[i] for i in range(0, len(file_list), 3)][:4]
        for f in file_list:
            if f not in to_keep:
                file_path = os.path.join(gallery_dir, f)
                base = os.path.splitext(f)[0]
                thumb_path = os.path.join(gallery_dir, f"{base}_thumb.webp")
                if os.path.exists(file_path): os.remove(file_path)
                if os.path.exists(thumb_path): os.remove(thumb_path)
                cursor.execute("DELETE FROM images WHERE file_name = ?", (f,))
                redundant_deleted += 1

    conn.commit()
    conn.close()
    
    print(f"✅ 任务完成！")
    print(f"🗑️  清理孤儿缩略图: {orphan_thumb} 张")
    print(f"🧹 移除数据库死链记录: {dead_db_count} 条")
    print(f"♻️  按采样规则删除冗余图: {redundant_deleted} 张")

if __name__ == "__main__":
    deep_clean_and_limit()
def delete_by_channel(channel_name):
    """
    【新增】按频道名彻底物理删除：原图 + 缩略图 + 数据库记录
    """
    if not os.path.exists(db_path): return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. 查找该频道的所有原图文件名
        cursor.execute("SELECT file_name FROM images WHERE channel = ?", (channel_name,))
        rows = cursor.fetchall()
        
        if not rows:
            print(f"ℹ️  库中未发现来自频道 [{channel_name}] 的图片。")
            conn.close()
            return

        print(f"🗑️  正在彻底清理频道 [{channel_name}]，共 {len(rows)} 组文件...")

        for row in rows:
            f = row[0]
            # 路径 A: 原图路径
            f_path = os.path.join(gallery_dir, f)
            # 路径 B: 缩略图路径
            base = os.path.splitext(f)[0]
            t_path = os.path.join(gallery_dir, f"{base}_thumb.webp")
            
            # 物理删除
            if os.path.exists(f_path): os.remove(f_path)
            if os.path.exists(t_path): os.remove(t_path)

        # 2. 数据库记录一键清除
        cursor.execute("DELETE FROM images WHERE channel = ?", (channel_name,))
        
        conn.commit()
        conn.close()
        print(f"✅ 频道 [{channel_name}] 已从硬盘和数据库中完全抹除。")

    except Exception as e:
        print(f"❌ 清理出错: {str(e)}")