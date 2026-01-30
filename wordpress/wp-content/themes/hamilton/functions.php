<?php
/**
 * PencilAI Gallery (Open Source Edition)
 *
 * This file replaces any payment/membership logic from the original site.
 *
 * License: GPL-2.0-or-later (recommended for WordPress themes)
 */

// Load theme style
add_action('wp_enqueue_scripts', function () {
    wp_enqueue_style('hamilton-style', get_stylesheet_uri());
});

/**
 * Get all images metadata for the gallery.
 *
 * Priority:
 *  1) PENCILAI_GALLERY_DB (wp-config.php constant)
 *  2) env PENCILAI_GALLERY_DB
 *  3) <wp-root>/scripts/gallery.db
 *
 * If SQLite is unavailable or DB not found, return empty array and the template
 * will fall back to scanning the tg_gallery directory.
 */
function penc_get_all_images(): array {
    if (!class_exists('SQLite3')) return [];

    $db_path = null;
    if (defined('PENCILAI_GALLERY_DB') && PENCILAI_GALLERY_DB) {
        $db_path = PENCILAI_GALLERY_DB;
    } elseif (getenv('PENCILAI_GALLERY_DB')) {
        $db_path = getenv('PENCILAI_GALLERY_DB');
    } else {
        $db_path = rtrim(ABSPATH, '/').'/scripts/gallery.db';
    }

    if (!$db_path || !file_exists($db_path)) return [];

    $rows = [];
    try {
        $db = new SQLite3($db_path);
        // Keep backward compatibility with your schema: images(id, channel, timestamp, file_name, captured_at)
        $res = $db->query('SELECT file_name, timestamp FROM images ORDER BY timestamp DESC');
        while ($res && ($row = $res->fetchArray(SQLITE3_ASSOC))) {
            if (!empty($row['file_name'])) $rows[] = $row;
        }
        $db->close();
    } catch (Throwable $e) {
        return [];
    }

    return $rows;
}
