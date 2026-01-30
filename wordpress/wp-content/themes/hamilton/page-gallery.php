<?php
/**
 * Template Name: PencilAI Gallery (Open Source)
 *
 * - Removes membership/paywall logic.
 * - Removes any hard-coded payment addresses/emails.
 * - Avoids absolute server paths by using ABSPATH/home_url.
 */

// ---------- i18n ----------
$lang = $_GET['lang'] ?? '';
if ($lang === '') {
    $browser_lang = substr($_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? 'en', 0, 2);
    $lang = ($browser_lang === 'zh') ? 'zh' : (($browser_lang === 'ja') ? 'jp' : 'en');
}
$lang = in_array($lang, ['en','zh','hk','jp'], true) ? $lang : 'en';

$texts = [
    'en' => ['title'=>'PencilAI Gallery', 'latest'=>'Latest', 'random'=>'Random', 'download'=>'Download', 'page'=>'Page', 'empty'=>'No images yet.'],
    'zh' => ['title'=>'铅笔爱画廊', 'latest'=>'最新发布', 'random'=>'随机浏览', 'download'=>'下载原图', 'page'=>'页', 'empty'=>'目录为空，还没有图片。'],
    'hk' => ['title'=>'鉛筆愛畫廊', 'latest'=>'最新發布', 'random'=>'隨機瀏覽', 'download'=>'下載原圖', 'page'=>'頁', 'empty'=>'目錄為空，還沒有圖片。'],
    'jp' => ['title'=>'PencilAI ギャラリー', 'latest'=>'新着順', 'random'=>'ランダム', 'download'=>'元画像DL', 'page'=>'ページ', 'empty'=>'画像がありません。'],
];
$t = $texts[$lang];

// ---------- helpers ----------
function penc_render_card(string $fn, array $t): void {
    $base_name = pathinfo($fn, PATHINFO_FILENAME);
    $thumb_fn = $base_name . '_thumb.webp';
    $display_fn = file_exists(ABSPATH . 'tg_gallery/' . $thumb_fn) ? $thumb_fn : $fn;
    $img_url = home_url('/tg_gallery/');

    echo '<div class="gallery-item-card">';
        echo '<div class="img-frame">';
            echo '<a href="' . esc_url($img_url.$fn) . '" target="_blank" rel="noopener">';
                echo '<img data-src="' . esc_url($img_url.$display_fn) . '" class="lazy-load" alt="" oncontextmenu="return false;">';
            echo '</a>';
        echo '</div>';
        echo '<div class="card-meta">';
            $fs = (file_exists(ABSPATH.'tg_gallery/'.$fn)) ? round(filesize(ABSPATH.'tg_gallery/'.$fn)/1024, 1) . 'KB' : '0KB';
            echo '<span class="file-size">' . esc_html($fs) . '</span>';
            echo '<a class="download-btn" href="' . esc_url($img_url.$fn) . '" download>' . esc_html($t['download']) . '</a>';
        echo '</div>';
    echo '</div>';
}

function penc_fallback_scan(): array {
    $dir = ABSPATH . 'tg_gallery/';
    if (!is_dir($dir)) return [];
    $files = glob($dir . '*.{jpg,jpeg,png,webp,gif}', GLOB_BRACE) ?: [];
    $files = array_values(array_filter($files, fn($p) => strpos($p, '_thumb.webp') === false));
    usort($files, fn($a,$b) => filemtime($b) <=> filemtime($a));
    return array_map(fn($p) => basename($p), $files);
}

// ---------- data ----------
$sort_mode = ($_GET['sort_mode'] ?? 'latest');
$sort_mode = in_array($sort_mode, ['latest','random'], true) ? $sort_mode : 'latest';
$seed = isset($_GET['seed']) ? intval($_GET['seed']) : 0;

$items_per_page = 15;
$current_page = max(1, intval($_GET['paged'] ?? 1));

$meta_rows = function_exists('penc_get_all_images') ? penc_get_all_images() : [];
$files = [];
if (!empty($meta_rows)) {
    foreach ($meta_rows as $r) {
        if (!empty($r['file_name'])) $files[] = $r['file_name'];
    }
} else {
    $files = penc_fallback_scan();
}

$total_files = count($files);

if ($sort_mode === 'random') {
    if ($seed <= 0) $seed = random_int(1, 999999);
    mt_srand($seed);
    for ($i = $total_files - 1; $i > 0; $i--) {
        $j = mt_rand(0, $i);
        $tmp = $files[$i];
        $files[$i] = $files[$j];
        $files[$j] = $tmp;
    }
}

$offset = ($current_page - 1) * $items_per_page;
$paged_files = array_slice($files, $offset, $items_per_page);
$total_pages = max(1, (int)ceil($total_files / $items_per_page));

?><!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?php echo esc_html($t['title']); ?></title>
    <?php wp_head(); ?>
    <style>
        html { margin-top: 0 !important; overflow-y: scroll; }
        #wpadminbar { display: none !important; }
        nav { position: fixed; top: 0; left: 0; right: 0; z-index: 1000; background: rgba(255,255,255,0.95); backdrop-filter: blur(5px); border-bottom: 1px solid #f2f2f2; height: 60px; display: flex; align-items: center; justify-content: space-between; padding: 0 40px; }
        nav a { text-decoration: none; color: #999; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
        nav a.active { color: #000; font-weight: bold; }
        .main-content-area { max-width: 1400px; margin: 80px auto 0; padding: 20px; }
        .gallery-grid { margin: 0 auto; min-height: 600px; }
        .gallery-item-card { width: 31%; margin-bottom: 40px; background: transparent; float: left; }
        .img-frame { background: #f4f4f4; border-radius: 4px; overflow: hidden; position: relative; min-height: 200px; transition: transform 0.3s ease, box-shadow 0.3s ease; }
        .img-frame:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.08); }
        .gallery-item-card img { width: 100%; display: block; max-height: 600px; object-fit: cover; object-position: top; opacity: 0; transition: opacity 0.5s ease; }
        .gallery-item-card img.loaded { opacity: 1; }
        .card-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; padding: 0 4px; }
        .file-size { font-size: 10px; color: #ccc; }
        .download-btn { border: none; border-bottom: 1px solid transparent; color: #333; font-size: 10px; font-weight: bold; padding-bottom: 1px; cursor: pointer; text-decoration: none; }
        .download-btn:hover { border-bottom-color: #333; }
        .pagination-wrapper { margin: 80px 0; display: flex; justify-content: center; align-items: center; gap: 10px; position: relative; z-index: 200; clear: both; }
        .pg-item { border: 1px solid #000; height: 32px; padding: 0 15px; display: inline-flex; align-items: center; justify-content: center; color: #000; text-decoration: none; font-size: 11px; font-weight: bold; box-sizing: border-box; }
        @media (max-width: 800px) { .gallery-item-card { width: 47%; } nav { padding: 0 20px; } }
    </style>
</head>
<body <?php body_class(); ?>>

<nav>
    <div style="display:flex; gap:16px; align-items:center;">
        <a href="?action=gallery&lang=<?php echo esc_attr($lang); ?>" style="color:#000; font-weight:bold; letter-spacing:2px;"><?php echo esc_html($t['title']); ?></a>
        <a href="?action=gallery&lang=<?php echo esc_attr($lang); ?>&sort_mode=latest" class="<?php echo $sort_mode==='latest'?'active':''; ?>"><?php echo esc_html($t['latest']); ?></a>
        <a href="?action=gallery&lang=<?php echo esc_attr($lang); ?>&sort_mode=random&seed=<?php echo (int)random_int(1,999999); ?>" class="<?php echo $sort_mode==='random'?'active':''; ?>"><?php echo esc_html($t['random']); ?></a>
    </div>
    <div style="display:flex; gap:12px; align-items:center;">
        <?php
        $langs = ['en'=>'EN','zh'=>'简','hk'=>'繁','jp'=>'JP'];
        foreach ($langs as $k=>$v) {
            $params = $_GET;
            $params['lang'] = $k;
            if (!isset($params['action'])) $params['action'] = 'gallery';
            $link = '?' . http_build_query($params);
            $cls = ($lang===$k) ? 'active' : '';
            echo '<a class="'.$cls.'" href="'.esc_url($link).'">'.esc_html($v).'</a>';
        }
        ?>
    </div>
</nav>

<div class="main-content-area">
    <div id="gallery-container" class="gallery-grid">
        <?php
        if (empty($paged_files)) {
            echo '<p style="color:#999; font-size:12px;">' . esc_html($t['empty']) . '</p>';
        } else {
            foreach ($paged_files as $fn) {
                penc_render_card($fn, $t);
            }
        }
        ?>
    </div>

    <div class="pagination-wrapper">
        <?php
        $base = '?action=gallery&lang=' . rawurlencode($lang) . '&sort_mode=' . rawurlencode($sort_mode);
        if ($sort_mode === 'random') $base .= '&seed=' . (int)$seed;
        if ($current_page > 1) {
            echo '<a class="pg-item" href="'.esc_url($base.'&paged='.($current_page-1)).'">PREV</a>';
        }
        echo '<span style="font-size:12px; color:#bbb;">' . (int)$current_page . ' / ' . (int)$total_pages . '</span>';
        if ($current_page < $total_pages) {
            echo '<a class="pg-item" href="'.esc_url($base.'&paged='.($current_page+1)).'">NEXT</a>';
        }
        ?>
        <div style="display:flex; align-items:center; gap:5px; margin-left: 15px;">
            <input type="number" id="jump_page" style="width:45px; height:32px; border:1px solid #000; text-align:center; padding:0; box-sizing:border-box; font-size:11px; font-weight:bold;" min="1" max="<?php echo (int)$total_pages; ?>" value="<?php echo (int)$current_page; ?>">
            <button class="pg-item" style="background:#000; color:#fff; cursor:pointer; height:32px; padding:0 15px; border:none;" onclick="var p=document.getElementById('jump_page').value; if(p>0 && p<=<?php echo (int)$total_pages; ?>){ window.location.href='<?php echo esc_js($base); ?>&paged='+p; }">GO</button>
        </div>
    </div>
</div>

<script src="https://unpkg.com/masonry-layout@4/dist/masonry.pkgd.min.js"></script>
<script src="https://unpkg.com/imagesloaded@5/imagesloaded.pkgd.min.js"></script>
<script>
document.addEventListener("DOMContentLoaded", function() {
    var grid = document.querySelector('#gallery-container');
    if(!grid) return;

    var msnry = new Masonry(grid, {
        itemSelector: '.gallery-item-card',
        columnWidth: '.gallery-item-card',
        percentPosition: true,
        gutter: 30
    });

    function debounce(func, wait) {
        let timeout;
        return function() {
            clearTimeout(timeout);
            const args = arguments;
            timeout = setTimeout(() => func.apply(null, args), wait);
        };
    }

    const debouncedLayout = debounce(function() { msnry.layout(); }, 100);

    imagesLoaded(grid).on('progress', function() {
        debouncedLayout();
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const img = entry.target;
            img.src = img.dataset.src;
            img.onload = () => { img.classList.add('loaded'); debouncedLayout(); };
            observer.unobserve(img);
        });
    }, { rootMargin: '1200px' });

    document.querySelectorAll('img.lazy-load').forEach(img => observer.observe(img));
});
</script>
<?php wp_footer(); ?>
</body>
</html>
