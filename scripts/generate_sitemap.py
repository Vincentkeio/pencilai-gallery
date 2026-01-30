"""Generate a simple sitemap for the gallery.

This open-source version DOES NOT ship any Google Indexing API key.
If you want to push URLs with Indexing API, provide a service account key file yourself
and set environment variables.

Env vars:
  - PENCILAI_GALLERY_DB: path to gallery.db
  - PENCILAI_SITEMAP_PATH: output sitemap path (default: ../sitemap_gallery.xml)
  - PENCILAI_BASE_URL: base site url, e.g. https://example.com/
  - PENCILAI_GOOGLE_INDEXING_KEY: optional service account json key file
"""

import os
import sqlite3
import datetime
import json

PER_PAGE = int(os.environ.get('PENCILAI_PER_PAGE', '15'))
DB_PATH = os.environ.get('PENCILAI_GALLERY_DB', os.path.join(os.path.dirname(__file__), 'gallery.db'))
SITEMAP_PATH = os.environ.get('PENCILAI_SITEMAP_PATH', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sitemap_gallery.xml')))
BASE_URL = os.environ.get('PENCILAI_BASE_URL', 'http://localhost/')
KEY_PATH = os.environ.get('PENCILAI_GOOGLE_INDEXING_KEY', '')


def generate_sitemap():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"DB not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM images')
    total_images = cur.fetchone()[0]
    conn.close()

    total_pages = (total_images // PER_PAGE) + 1
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d')

    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for p in range(1, total_pages + 1):
        priority = '0.9' if p <= 10 else '0.6'
        loc = f"{BASE_URL}?action=gallery&paged={p}"
        xml.append(f"  <url><loc>{loc}</loc><lastmod>{now}</lastmod><priority>{priority}</priority></url>")

    xml.append('</urlset>')

    with open(SITEMAP_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(xml))

    return total_pages


def push_to_google(urls):
    # Optional: only if user provides a key file
    if not KEY_PATH or not os.path.exists(KEY_PATH):
        print('No indexing key provided, skip push.')
        return

    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession

        scopes = ['https://www.googleapis.com/auth/indexing']
        credentials = service_account.Credentials.from_service_account_file(KEY_PATH, scopes=scopes)
        session = AuthorizedSession(credentials)
        endpoint = 'https://indexing.googleapis.com/v3/urlNotifications:publish'

        for url in urls:
            data = json.dumps({'url': url, 'type': 'URL_UPDATED'})
            r = session.post(endpoint, data=data)
            print(url, r.status_code)
    except Exception as e:
        print('Push failed:', e)


if __name__ == '__main__':
    pages = generate_sitemap()
    print(f"Sitemap created: {pages} pages -> {SITEMAP_PATH}")
    # Push newest 20 pages
    base = BASE_URL.rstrip('/') + '/'
    urls = [f"{base}?action=gallery&paged={p}" for p in range(1, min(21, pages + 1))]
    push_to_google(urls)
