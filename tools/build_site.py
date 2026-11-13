"""かくれんぼスレの静的サイトを docs/ に組み立てて、全スレを自動テストする。
usage: python3 tools/build_site.py
- threads.json に並んだスレを threads/<slug>/spec.json から生成
- docs/kakurenbo/<slug>/index.html と og.png（リンクカード）を出力
- threads/<slug>/post.png（X投稿用の画像）を出力
- 全スレで「全語を書き込む → 100% & クリア画面」をヘッドレスブラウザで確認（失敗したら止まる）
"""
import json, os, shutil, subprocess, html, sys
from playwright.sync_api import sync_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(REPO, 'tools')
DOCS = os.path.join(REPO, 'docs')
# 独自ドメインを使うときは CUSTOM_DOMAIN = 'hownever.com' にする（CNAMEが出力され、URLも切り替わる）
CUSTOM_DOMAIN = ''
SITE_ROOT = f'https://{CUSTOM_DOMAIN}/' if CUSTOM_DOMAIN else 'https://gaasuu8910.github.io/'
BASE = SITE_ROOT + 'kakurenbo/'
SCHEDULE = '火・金・日の21時'  # 次スレの更新曜日・時刻（サイト全体に表示）
# アクセス解析（Googleアナリティクス4）の測定ID。空なら解析タグを入れない
GA_ID = ''
def ga_inject(path):
    if not GA_ID: return
    h = open(path, encoding='utf-8').read()
    tag = (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>'
           f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA_ID}');</script>")
    h = h.replace('<!--GA-->', tag, 1).replace('<!--GANOTE-->', '<br>※アクセス解析にGoogleアナリティクスを使っています（Cookieを使用）', 1)
    if '</head>' in h and tag not in h: h = h.replace('</head>', tag + '\n</head>', 1)
    open(path, 'w', encoding='utf-8').write(h)
CHROME = os.environ.get('CHROME', '/usr/bin/google-chrome')

threads = json.load(open(os.path.join(REPO, 'threads.json'), encoding='utf-8'))
shutil.rmtree(DOCS, ignore_errors=True)
os.makedirs(os.path.join(DOCS, 'kakurenbo'))

rows, failed = [], []
with sync_playwright() as pw:
    launch = {'executable_path': CHROME} if os.path.exists(CHROME) else {}
    b = pw.chromium.launch(**launch)
    for t in threads:
        src = os.path.join(REPO, 'threads', t['slug'])
        sp_path = os.path.join(src, 'spec.json')
        sp = json.load(open(sp_path, encoding='utf-8'))
        url = BASE + t['slug'] + '/'
        sp['page_url'] = url
        sp['share_url'] = url
        sp['next_schedule'] = SCHEDULE
        json.dump(sp, open(sp_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        out = os.path.join(DOCS, 'kakurenbo', t['slug'])
        subprocess.run([sys.executable, os.path.join(TOOLS, 'gen.py'), sp_path, out], check=True)
        pg = b.new_page(viewport={'width': 1200, 'height': 630})
        pg.goto('file://' + os.path.join(out, 'og.html')); pg.locator('#c').screenshot(path=os.path.join(out, 'og.png'))
        pg = b.new_page(viewport={'width': 900, 'height': 1200}, device_scale_factor=1.5)
        pg.goto('file://' + os.path.join(out, 'poster.html')); pg.locator('#c').screenshot(path=os.path.join(src, 'post.png'))
        os.remove(os.path.join(out, 'og.html')); os.remove(os.path.join(out, 'poster.html'))
        # 自動テスト: 全語を書き込む → 100% とクリア画面
        pg = b.new_page(viewport={'width': 420, 'height': 860}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto('file://' + os.path.join(out, 'index.html'))
        pg.fill('#msg', ' '.join(sp['keys'].keys())); pg.click('.post-btn'); pg.wait_for_timeout(2300)
        prog = pg.inner_text('#prog-text'); ok = prog.startswith(f"{len(sp['keys'])} / {len(sp['keys'])}") and pg.is_visible('#clear') and not errs
        print(('OK  ' if ok else 'FAIL'), t['slug'], prog, errs)
        if not ok: failed.append(t['slug'])
        ga_inject(os.path.join(out, 'index.html'))
        rows.append((t['no'], t['slug'], sp['title'], sp['board'], sp['noun'], len(sp['keys']), t.get('date', '')))
    b.close()

rows.sort(key=lambda r: -r[0])
items = '\n'.join(
    f'<li><span class="no">{html.escape(noun)}</span> <a href="./{s}/">{html.escape(title)}</a><div class="meta">{html.escape(board)}／{html.escape(noun)}が{k}個かくれている／{d}</div></li>'
    for n, s, title, board, noun, k, d in rows)
desc = '2ちゃんねる風の書き込みに、言葉が20個かくれている。何%見つけられる？'
index = f'''<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>かくれんぼスレ 過去ログ一覧</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="かくれんぼスレ"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{BASE}"><meta name="twitter:card" content="summary"><meta name="twitter:site" content="@gaasuuquestion">
<!-- ANALYTICS -->
<style>
body{{margin:0;background:#efefef;font-family:"MS PGothic","Hiragino Kaku Gothic ProN","Noto Sans JP",sans-serif;color:#000}}
.w{{max-width:820px;margin:0 auto;padding:16px 14px 60px}}
h1{{color:#c00;font-size:24px;margin:10px 0 4px}}
.lead{{font-size:14px;color:#444;margin-bottom:18px}}
ul{{list-style:none;padding:0;margin:0;border-top:1px solid #ccc}}
li{{padding:12px 4px;border-bottom:1px dashed #ccc;font-size:16px}}
.no{{color:#008000;font-weight:bold}}
a{{color:#00e}}
.meta{{font-size:12px;color:#666;margin-top:2px}}
.foot{{margin-top:28px;font-size:12px;color:#666}}
</style></head><body><div class="w">
<div class="lead">■ かくれんぼスレ ■ 過去ログ一覧（どれからでも遊べます）</div>
<h1>かくれんぼスレ</h1>
<div class="lead">{desc}<br>毎週 {SCHEDULE} 更新｜<a href="https://x.com/intent/follow?screen_name=gaasuuquestion">@gaasuuquestion をフォロー</a></div>
<ul>
{items}
</ul>
<div class="foot">※各スレッドはフィクションの謎解きゲームです。<br>制作：ガースー/MICHI（<a href="https://x.com/gaasuuquestion">@gaasuuquestion</a>）</div>
</div></body></html>'''
open(os.path.join(DOCS, 'kakurenbo', 'index.html'), 'w', encoding='utf-8').write(index)
ga_inject(os.path.join(DOCS, 'kakurenbo', 'index.html'))
open(os.path.join(DOCS, 'index.html'), 'w', encoding='utf-8').write(
    '<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=kakurenbo/">'
    '<title>HOWNEVER</title></head><body><a href="kakurenbo/">かくれんぼスレ</a> / <a href="https://shop.hownever.com/">STORE</a></body></html>')
if CUSTOM_DOMAIN:
    open(os.path.join(DOCS, 'CNAME'), 'w').write(CUSTOM_DOMAIN + '\n')
open(os.path.join(DOCS, '.nojekyll'), 'w').write('')
print('site built:', [r[1] for r in rows])
if failed:
    sys.exit('TEST FAILED: ' + ', '.join(failed))
