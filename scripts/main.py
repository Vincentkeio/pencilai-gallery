import os
import asyncio
import shutil
import json
import time
import schedule
import sqlite3
from telethon import TelegramClient
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(BASE_DIR, 'config.json')


def load_config():
    cfg_path = os.environ.get('PENCILAI_CONFIG', DEFAULT_CONFIG)
    if not os.path.exists(cfg_path):
        raise FileNotFoundError(
            f"Config not found: {cfg_path}. Copy config.example.json to config.json and fill in your secrets."
        )
    with open(cfg_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS images
        (id TEXT PRIMARY KEY, channel TEXT, timestamp INTEGER, file_name TEXT, captured_at INTEGER)''')
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sort_flow ON images (captured_at, timestamp)")
    conn.commit()
    conn.close()


def save_to_db(db_path: str, msg_id, channel, timestamp, file_name, captured_at):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO images VALUES (?, ?, ?, ?, ?)",
                   (str(msg_id), channel, int(timestamp), file_name, captured_at))
    conn.commit()
    conn.close()


def load_set(path: str):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def append_line(path: str, line: str):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(line + "\n")


def load_json(path: str):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_json(path: str, obj):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False)


def check_and_clean_disk(save_path_root: str, min_free_gb: int = 5, target_free_gb: int = 10):
    usage = shutil.disk_usage(save_path_root)
    free_gb = usage.free / (1024 ** 3)
    if free_gb >= min_free_gb:
        return

    all_files = []
    for f in os.listdir(save_path_root):
        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
            p = os.path.join(save_path_root, f)
            all_files.append((p, os.path.getmtime(p)))
    all_files.sort(key=lambda x: x[1])

    for file_path, _ in all_files:
        try:
            os.remove(file_path)
            if shutil.disk_usage(save_path_root).free / (1024 ** 3) >= target_free_gb:
                break
        except Exception:
            pass


def create_thumbnail_1080p(image_path: str):
    target_width = 1080
    size_threshold = 300 * 1024
    try:
        if os.path.getsize(image_path) < size_threshold:
            return
        base, _ = os.path.splitext(image_path)
        thumb_path = f"{base}_thumb.webp"
        if os.path.exists(thumb_path):
            return
        with Image.open(image_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            if img.size[0] > target_width:
                w_percent = (target_width / float(img.size[0]))
                new_height = int(float(img.size[1]) * float(w_percent))
                img = img.resize((target_width, new_height), Image.Resampling.LANCZOS)
            img.save(thumb_path, "WEBP", quality=85)
    except Exception:
        pass


async def download_images(client, message_list, history_set, channel_name, group_id, batch_time,
                          save_path_root: str, history_file: str, db_path: str):
    for message in message_list:
        if not message.photo:
            continue

        msg_id_str = str(message.id)
        if msg_id_str in history_set:
            continue

        file_name = f"photo_{channel_name}_{message.date.strftime('%Y-%m-%d_%H-%M-%S')}_{group_id}_{message.id}.jpg"
        full_path = os.path.join(save_path_root, file_name)

        if os.path.exists(full_path):
            append_line(history_file, msg_id_str)
            history_set.add(msg_id_str)
            save_to_db(db_path, msg_id_str, channel_name, message.date.timestamp(), file_name, batch_time)
            continue

        check_and_clean_disk(save_path_root)
        try:
            await client.download_media(message, file=full_path)
            print(f"      ✅ downloaded: {file_name}")
            append_line(history_file, msg_id_str)
            history_set.add(msg_id_str)
            save_to_db(db_path, msg_id_str, channel_name, message.date.timestamp(), file_name, batch_time)
            create_thumbnail_1080p(full_path)
        except Exception as e:
            print(f"      ❌ download failed: {e}")


async def process_group_buffer(client, buffer, history_set, channel_name, batch_time,
                               save_path_root: str, history_file: str, db_path: str):
    if not buffer:
        return
    g_id = buffer[0].grouped_id if buffer[0].grouped_id else f"S{buffer[0].id}"
    sorted_msgs = sorted(buffer, key=lambda x: x.id)
    total = len(sorted_msgs)
    targets = [sorted_msgs[i] for i in range(0, total, 3)][:4]
    print(f"  📦 group {g_id}: {total} photos -> sampled {len(targets)}")
    await download_images(client, targets, history_set, channel_name, g_id, batch_time,
                          save_path_root, history_file, db_path)


async def process_channel(client, channel_name, last_ids: dict, history_set, batch_time,
                          save_path_root: str, history_file: str, db_path: str, limit_count: int):
    min_id = int(last_ids.get(channel_name, 0) or 0)
    current_group_buffer = []
    current_grouped_id = None
    new_max_id = min_id

    print(f"📡 scanning {channel_name} (from id {min_id})")

    async for message in client.iter_messages(channel_name, limit=limit_count, min_id=min_id):
        new_max_id = max(new_max_id, message.id)

        if message.photo:
            if message.grouped_id:
                if current_grouped_id != message.grouped_id:
                    if current_group_buffer:
                        await process_group_buffer(client, current_group_buffer, history_set, channel_name, batch_time,
                                                   save_path_root, history_file, db_path)
                    current_grouped_id = message.grouped_id
                    current_group_buffer = [message]
                else:
                    current_group_buffer.append(message)
            else:
                if current_group_buffer:
                    await process_group_buffer(client, current_group_buffer, history_set, channel_name, batch_time,
                                               save_path_root, history_file, db_path)
                    current_group_buffer = []
                    current_grouped_id = None
                await download_images(client, [message], history_set, channel_name, f"S{message.id}", batch_time,
                                      save_path_root, history_file, db_path)
        else:
            if current_group_buffer:
                await process_group_buffer(client, current_group_buffer, history_set, channel_name, batch_time,
                                           save_path_root, history_file, db_path)
                current_group_buffer = []
                current_grouped_id = None

    if current_group_buffer:
        await process_group_buffer(client, current_group_buffer, history_set, channel_name, batch_time,
                                   save_path_root, history_file, db_path)

    if new_max_id > min_id:
        last_ids[channel_name] = new_max_id


async def run_task_once(cfg: dict):
    tg = cfg['telegram']
    paths = cfg['paths']

    api_id = int(tg['api_id'])
    api_hash = str(tg['api_hash'])
    phone_number = str(tg['phone_number'])
    two_step_password = str(tg.get('two_step_password') or '')

    channels = tg.get('channels', [])
    limit_count = int(tg.get('limit_count', 5000))

    site_root = os.path.abspath(os.path.join(BASE_DIR, paths.get('site_root', '..')))
    save_path_root = os.path.abspath(os.path.join(BASE_DIR, paths.get('tg_gallery_dir', '../tg_gallery')))
    db_path = os.path.abspath(os.path.join(BASE_DIR, paths.get('db_path', './gallery.db')))

    session_file = os.path.abspath(os.path.join(BASE_DIR, paths.get('session_file', './anon')))
    timer_config = os.path.abspath(os.path.join(BASE_DIR, paths.get('timer_config', './timer_config.json')))
    last_ids_path = os.path.abspath(os.path.join(BASE_DIR, paths.get('last_ids', './last_ids.json')))
    history_file = os.path.abspath(os.path.join(BASE_DIR, paths.get('download_history', './download_history.txt')))

    os.makedirs(save_path_root, exist_ok=True)
    init_db(db_path)

    history_set = load_set(history_file)
    last_ids = load_json(last_ids_path)

    batch_time = int(time.time())

    client = TelegramClient(session_file, api_id, api_hash)
    await client.start(phone=phone_number, password=(two_step_password or None))

    async with client:
        for ch in channels:
            try:
                await process_channel(client, ch, last_ids, history_set, batch_time,
                                      save_path_root, history_file, db_path, limit_count)
            except Exception as e:
                print(f"❌ channel {ch} failed: {e}")

    save_json(last_ids_path, last_ids)


async def run_daemon(cfg: dict):
    timer_path = os.path.abspath(os.path.join(BASE_DIR, cfg['paths'].get('timer_config', './timer_config.json')))

    if not os.path.exists(timer_path):
        conf = {"mode": "interval", "days": 0, "hours": 6, "mins": 0}
        save_json(timer_path, conf)
    else:
        conf = load_json(timer_path)

    schedule.clear()

    def job():
        asyncio.create_task(run_task_once(cfg))

    if conf.get('mode') == 'daily':
        schedule.every().day.at(conf['time']).do(job)
    else:
        total_m = max(int(conf.get('days', 0)) * 1440 + int(conf.get('hours', 0)) * 60 + int(conf.get('mins', 0)), 1)
        schedule.every(total_m).minutes.do(job)

    await run_task_once(cfg)

    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


if __name__ == '__main__':
    import sys

    cfg = load_config()
    mode = sys.argv[1] if len(sys.argv) > 1 else 'once'

    if mode == 'daemon':
        asyncio.run(run_daemon(cfg))
    else:
        asyncio.run(run_task_once(cfg))
