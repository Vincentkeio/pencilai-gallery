import sqlite3
import json
import time
import os
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


# 数据库路径
def migrate_and_init():
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在，请确认路径。")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🚀 启动数据库按需修复与优化...")

    # --- 1. 结构检查：添加字段 ---
    try:
        cursor.execute("ALTER TABLE images ADD COLUMN captured_at INTEGER")
        print("✅ 成功添加 captured_at 字段。")
    except sqlite3.OperationalError:
        print("ℹ️  captured_at 字段已存在。")

    # --- 2. 区别对待：仅初始化未赋值的入库时间 ---
    # 检查还有多少图片没有入库时间
    cursor.execute("SELECT COUNT(*) FROM images WHERE captured_at IS NULL")
    missing_count = cursor.fetchone()[0]

    if missing_count > 0:
        current_now = int(time.time())
        print(f"⏳ 发现 {missing_count} 张图片缺失入库时间，正在初始化为: {current_now} ...")
        # 🌟 关键修改：只更新为 NULL 的记录
        cursor.execute("UPDATE images SET captured_at = ? WHERE captured_at IS NULL", (current_now,))
        print(f"✅ 已补全 {missing_count} 条记录。")
    else:
        print("ℹ️  所有图片均已有入库时间，跳过初始化。")

    # --- 3. 索引检查：自动判断是否存在 ---
    # CREATE INDEX IF NOT EXISTS 是最优实践，它会自动检测是否存在
    print("⚡ 正在检查并维护复合排序索引 (idx_sort_flow)...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sort_flow ON images (captured_at, timestamp)")
    
    # --- 4. 物理清理 (VACUUM) ---
    print("🧹 正在整理数据库物理空间...")
    cursor.execute("VACUUM")
    
    conn.commit()
    conn.close()
    
    print("-" * 50)
    print(f"✅ 数据库优化任务完成！")
    print(f"🚀 索引状态：已就绪（按需建立）。")
    print(f"📊 数据状态：已补全（跳过已有值）。")

if __name__ == "__main__":
    migrate_and_init()