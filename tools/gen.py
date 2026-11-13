"""かくれんぼスレジェネレーター
usage: python3 gen.py spec.json outdir
spec.json: title, board, noun, op_name, op_id, op_date, body(file), replies[[id,text]...],
           keys{key:[aliases]}, labels{key:label}, near{word:reply}, foot, store, share_url
body: {表示|読み} で隠し言葉をマーク"""
import json, re, sys, html, os

MARK = re.compile(r'\{([^|{}]+)\|([^{}]+)\}')
here = os.path.dirname(os.path.abspath(__file__))

def main():
    spec_path, outdir = sys.argv[1], sys.argv[2]
    base = os.path.dirname(os.path.abspath(spec_path))
    sp = json.load(open(spec_path, encoding='utf-8'))
    body = open(os.path.join(base, sp['body']), encoding='utf-8').read().strip()
    marks = sorted(set(k for _, k in MARK.findall(body)))
    keys = sp['keys']
    assert sorted(keys) == sorted(set(marks) | ({sp['op_id_key']} if sp.get('op_id_key') else set())), f'keys mismatch: {set(keys) ^ set(marks)}'

    def mark(m):
        return f'<span class="n" data-k="{html.escape(m.group(2))}">{html.escape(m.group(1))}</span>'
    parts, last = [], 0
    for m in MARK.finditer(body):
        parts.append(html.escape(body[last:m.start()])); parts.append(mark(m)); last = m.end()
    parts.append(html.escape(body[last:]))
    op_html = ''.join(parts)

    nm = html.escape(sp['op_name'])
    op_id_html = html.escape(sp['op_id'])
    if sp.get('op_id_key'):
        op_id_html = f'<span class="n" data-k="{sp["op_id_key"]}">{op_id_html}</span>'
        marks = sorted(set(marks) | {sp['op_id_key']})
        assert sorted(keys) == marks, 'keys mismatch (id)'
    posts = [f'''    <div class="post" id="r1">
      <div class="head"><span class="no">1</span> 名前：<span class="nm">{nm}</span> 投稿日：{sp['op_date']} ID:{op_id_html}</div>
      <div class="body" id="op">{op_html}</div>
    </div>''']
    for i, (rid, date, text) in enumerate(sp.get('replies', []), start=2):
        posts.append(f'''    <div class="post">
      <div class="head"><span class="no">{i}</span> 名前：<span class="nm">{nm}</span> 投稿日：{date} ID:{rid}</div>
      <div class="body">{html.escape(text)}</div>
    </div>''')

    t = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
    js = lambda v: json.dumps(v, ensure_ascii=False)
    rep = {
        'DESC': html.escape(f"この書き込みに、{sp['noun']}が{len(keys)}個隠れています。何%見つけられる？ #かくれんぼスレ"),
        'PAGE_URL': html.escape(sp.get('page_url', '')),
        'TITLE': html.escape(sp['title']), 'BOARD': html.escape(sp['board']), 'NOUN': html.escape(sp['noun']),
        'TOTAL': str(len(keys)), 'RESCOUNT': str(1 + len(sp.get('replies', []))), 'THREAD': '\n'.join(posts),
        'FOOT': html.escape(sp['foot']), 'SHARE_URL': js(sp.get('share_url', '')), 'QUOTE_URL': js(sp.get('quote_url', '')), 'NEXT': html.escape(sp.get('next_schedule', '月・金の21時')), 'KEYS': js(keys),
        'LABEL': js(sp['labels']), 'NEAR': js(sp.get('near', {})), 'MISS': sp.get('miss_verb', 'ない'), 'LEVELS': js(sp.get('levels', {})), 'SPECIAL': js(sp.get('special', {})), 'OP_NAME_JS': js(sp['op_name']),
        'OP_ID_JS': js(sp['op_id']), 'STORE': js(sp['store']),
    }
    for k, v in rep.items():
        t = t.replace('{{' + k + '}}', v)
    t = t.replace('let resNo = 4;', f'let resNo = {1 + len(sp.get("replies", []))};')
    assert '{{' not in t
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'index.html'), 'w', encoding='utf-8').write(t)

    # X投稿用画像のHTML
    plain = html.escape(MARK.sub(lambda m: m.group(1), body))
    poster = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0;background:#efefef;font-family:"Noto Sans JP","Hiragino Kaku Gothic ProN",sans-serif}}
.c{{width:900px;padding:40px 48px 36px;box-sizing:border-box}}
.b{{font-size:20px;color:#666;border-bottom:1px solid #ccc;padding-bottom:10px}}
h1{{color:#c00;font-size:30px;line-height:1.4;margin:18px 0}}
.h{{font-size:20px;color:#555}} .nm{{color:#008000;font-weight:bold}}
.t{{white-space:pre-wrap;font-size:27px;line-height:1.72;margin:10px 0 0 22px}}
.q{{margin-top:22px;background:#fff;border:2px solid #c00;padding:14px 18px;font-size:26px;font-weight:bold;color:#c00;text-align:center}}
</style></head><body><div class="c" id="c">
<div class="b">■ かくれんぼスレ ■ {html.escape(sp['board'])}</div>
<h1>{html.escape(sp['title'])}</h1>
<div class="h">1 名前：<span class="nm">{nm}</span> 投稿日：{sp['op_date']} ID:{sp['op_id']}</div>
<div class="t">{plain}</div>
<div class="q">&gt;&gt;1のどこかに、{html.escape(sp['noun'])}が{len(keys)}個隠れています。</div>
</div></body></html>'''
    open(os.path.join(outdir, 'poster.html'), 'w', encoding='utf-8').write(poster)
    og = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0}}
.o{{width:1200px;height:630px;background:#efefef;box-sizing:border-box;padding:56px 70px;font-family:"Noto Sans JP",sans-serif;display:flex;flex-direction:column;justify-content:space-between;border:14px solid #c00}}
.b{{font-size:30px;color:#666}}
.t{{font-size:54px;font-weight:bold;color:#c00;line-height:1.35}}
.q{{font-size:40px;font-weight:bold;color:#111}}
.q span{{background:#ffe14d;padding:0 8px}}
</style></head><body><div class="o" id="c">
<div class="b">■ かくれんぼスレ ■ {html.escape(sp['board'])}</div>
<div class="t">{html.escape(sp['title'])}</div>
<div class="q">この書き込みに、<span>{html.escape(sp['noun'])}が{len(keys)}個</span>隠れています。</div>
</div></body></html>'''
    open(os.path.join(outdir, 'og.html'), 'w', encoding='utf-8').write(og)
    print('generated', outdir, len(keys), 'keys')

main()
