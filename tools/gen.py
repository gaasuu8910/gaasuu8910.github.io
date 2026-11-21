"""かくれんぼスレジェネレーター
usage: python3 gen.py spec.json outdir
spec.json: title, board, noun, op_name, op_id, op_date, body(file), replies[[id,text]...],
           keys{key:[aliases]}, labels{key:label}, near{word:reply}, foot, store, share_url
body: {表示|読み} で隠し言葉をマーク"""
import json, re, sys, html, os

MARK = re.compile(r'\{([^|{}]+)\|([^{}]+)\}')
here = os.path.dirname(os.path.abspath(__file__))

def sfx_uri(name):
    import base64
    f = os.path.join(here, 'sfx', name)
    return ('data:audio/mpeg;base64,' + base64.b64encode(open(f, 'rb').read()).decode()) if os.path.exists(f) else ''

def main():
    spec_path, outdir = sys.argv[1], sys.argv[2]
    base = os.path.dirname(os.path.abspath(spec_path))
    sp = json.load(open(spec_path, encoding='utf-8'))
    body = open(os.path.join(base, sp['body']), encoding='utf-8').read().strip()
    # スレタイ・名前欄にも {表示|読み} で隠し語を置ける（高難度隠し用）
    def mk_html(text):
        out, last = [], 0
        for m in MARK.finditer(text):
            out.append(html.escape(text[last:m.start()])); out.append(f'<span class="n" data-k="{html.escape(m.group(2))}">{html.escape(m.group(1))}</span>'); last = m.end()
        return ''.join(out) + html.escape(text[last:])
    title_raw, name_raw, date_raw = sp['title'], sp['op_name'], sp['op_date']
    late = sp.get('late_reply')
    end1000 = sp.get('end_1000')
    reply_raw = ''.join(r[2] for r in sp.get('replies', [])) + (late['text'] if late else '') + (end1000['text'] if end1000 else '')
    outer_marks = set(k for _, k in MARK.findall(title_raw + name_raw + date_raw + reply_raw))
    sp['op_date'] = MARK.sub(lambda m: m.group(1), date_raw)
    sp['title'] = MARK.sub(lambda m: m.group(1), title_raw); sp['op_name'] = MARK.sub(lambda m: m.group(1), name_raw)
    marks = sorted(set(x for _, k in MARK.findall(body) for x in k.split('/')) | outer_marks)
    keys = sp['keys']
    ph_raw = sp.get('placeholder', '')
    ph_keys = set(x for _, k in MARK.findall(ph_raw) for x in k.split('/'))
    extra_keys = ({sp['op_id_key']} if sp.get('op_id_key') else set()) | ({sp['tab_title']['key']} if sp.get('tab_title') else set()) | ph_keys | ({sp['twist']['key']} if sp.get('twist',{}).get('key') else set()) | ({sp['scratch']['key']} if sp.get('scratch') else set()) | ({sp['mirror']['key']} if sp.get('mirror') else set()) | ({m[1] for m in MARK.findall(sp['mirror'].get('button',''))} if sp.get('mirror') else set())
    assert sorted(keys) == sorted(set(marks) | extra_keys), f'keys mismatch: {set(keys) ^ (set(marks) | extra_keys)}'

    def mark(m):
        inner = html.escape(m.group(1))
        for k in reversed(m.group(2).split('/')):
            inner = f'<span class="n" data-k="{html.escape(k)}">{inner}</span>'
        return inner
    parts, last = [], 0
    for m in MARK.finditer(body):
        parts.append(html.escape(body[last:m.start()])); parts.append(mark(m)); last = m.end()
    parts.append(html.escape(body[last:]))
    op_html = ''.join(parts).replace('[[', '<span class="inv">').replace(']]', '</span>')
    OMIT = '&lt;&lt;省略&gt;&gt;'
    if OMIT in op_html:
        a, b = op_html.split(OMIT, 1)
        op_html = (a + '<span class="omitbox"><br><a href="#" class="omit-link">省略されました・・全てを読むにはここを押してください</a></span>'
                   + '<span class="omit-rest" hidden>' + b + '</span>')

    if sp.get('scratch'):
        S = sp['scratch']
        card = lambda inner, cv: f'<div class="sc-card"><div class="sc-h">{html.escape(S.get("name","スクラッチ"))}</div><div class="sc-win">{inner}</div>{cv}</div>'
        op_html += ('<div class="scratch">' + card('ハズレ', '') + card('ハズレ', '')
                    + card(f'<span class="n" data-k="{html.escape(S["key"])}">{html.escape(S["label"])}</span>', '<canvas class="sc-cv"></canvas>') + '</div>')
    if sp.get('mirror'):
        M = sp['mirror']
        mirror_div = f'<div class="mirror"><span class="n mtxt" data-k="{html.escape(M["key"])}">{html.escape(M["text"])}</span></div>'
        if M.get('button'):
            op_html += f'<button type="button" class="imgbtn" onclick="openImg()">🖼 画像を開く：{mk_html(M["button"])}</button><div class="imgmodal" id="imgmodal" onclick="this.classList.remove(\'on\')"><div class="imgbox">{mirror_div}<div class="imgclose">タップで閉じる</div></div></div>'
        else:
            op_html += mirror_div
    nm = mk_html(name_raw)
    op_id_html = html.escape(sp['op_id'])
    if sp.get('op_id_key'):
        op_id_html = f'<span class="n" data-k="{sp["op_id_key"]}">{op_id_html}</span>'
        marks = sorted(set(marks) | {sp['op_id_key']})
        assert sorted(keys) == marks, 'keys mismatch (id)'
    posts = [f'''    <div class="post" id="r1">
      <div class="head"><span class="no">1</span> 名前：<span class="nm">{nm}</span> 投稿日：{mk_html(date_raw)} ID:{op_id_html}</div>
      <div class="body" id="op">{op_html}</div>
    </div>''']
    for i, (rid, date, text) in enumerate(sp.get('replies', []), start=2):
        posts.append(f'''    <div class="post">
      <div class="head"><span class="no">{i}</span> 名前：<span class="nm">{nm}</span> 投稿日：{date} ID:{rid}</div>
      <div class="body">{mk_html(text)}</div>
    </div>''')

    late_info = None
    if late:
        lk = MARK.findall(late['text'])[0][1]
        late_info = {'after_sec': late.get('after_sec', 240), 'key': lk}
        posts.append(f'''    <div class="post late" id="late" hidden>
      <div class="head"><span class="no"></span> 名前：<span class="nm">{nm}</span> 投稿日：{late['date']} ID:{late['id']}</div>
      <div class="body">{mk_html(late['text'])}</div>
    </div>''')

    if end1000:
        ek = MARK.findall(end1000['text'])[-1][1]
        posts.append('    <div class="post skip">（中略）</div>')
        posts.append(f'''    <div class="post">
      <div class="head"><span class="no">1000</span> 名前：<span class="nm">{nm}</span> 投稿日：{end1000['date']} ID:{end1000['id']}</div>
      <div class="body">{mk_html(end1000['text'])}</div>
    </div>''')
        posts.append(f'''    <div class="post">
      <div class="head"><span class="no">1001</span> 名前：<span class="nm" style="color:#c00">1001</span> 投稿日：Over 1000 Thread</div>
      <div class="body"><span class="n" data-k="{ek}">こ</span>のスレッドは1000を超えました。
もう書けないので、新しいスレッドを立ててくださいです。。。</div>
    </div>''')
    others = []
    try:
        repo = os.path.dirname(here)
        for th in sorted(json.load(open(os.path.join(repo, 'threads.json'), encoding='utf-8')), key=lambda x: -x['no']):
            if th['slug'] == os.path.basename(base): continue
            osp = json.load(open(os.path.join(repo, 'threads', th['slug'], 'spec.json'), encoding='utf-8'))
            others.append({'slug': th['slug'], 'title': MARK.sub(lambda m: m.group(1), osp['title']), 'noun': osp['noun'],
                           'total': len(osp['keys']), 'counter': osp.get('counter', '個'), 'store': osp['store'], 'diff': osp.get('difficulty', 2), 'no': th.get('no', 0)})
    except Exception as e:
        print('others skipped:', e)
    # ヒント（毎週木曜に解禁）: 言葉ごとに「どこを見るか」を作る
    import datetime
    blines = body.split('\n'); nb = len(blines)
    HMSG = {'body': '光っている行のどこかに、かくれている', 'title': 'スレタイ（いちばん上の赤い文字）をよく見てみよう',
            'head': '1の投稿の名前欄や日付をよく見てみよう', 'id': '1の投稿のIDをよく見てみよう',
            'replies': '1の投稿だけじゃない。レス（2以降）に目を向けよう', 'late': 'このスレを開いたまま、しばらく待ってみよう',
            'tab': 'このスレを開いたまま、別のタブに切り替えてみよう', 'input': '書き込み欄の薄い文字を、よく読んでみよう'}
    hints = {}
    span = {}
    for m in MARK.finditer(body):
        a, b = body[:m.start()].count('\n'), body[:m.end()].count('\n')
        for k in m.group(2).split('/'):
            if k in span: span[k] = (min(span[k][0], a), max(span[k][1], b))
            else: span[k] = (a, b)
    for k, (a, b) in span.items():
        if b - a < 1:
            a0 = max(0, a - (len(k) % 2)); b0 = min(nb - 1, a0 + 2); a0 = max(0, b0 - 2)
            a, b = a0, b0
        hints[k] = {'place': 'body', 'lines': [a, b]}
    for raw, place in ((title_raw, 'title'), (name_raw + date_raw, 'head'), (''.join(r[2] for r in sp.get('replies', [])), 'replies')):
        for _, kk in MARK.findall(raw):
            for k in kk.split('/'): hints.setdefault(k, {'place': place})
    if late:
        for _, kk in MARK.findall(late['text']):
            for k in kk.split('/'): hints[k] = {'place': 'late'}
    if sp.get('op_id_key'): hints[sp['op_id_key']] = {'place': 'id'}
    if sp.get('tab_title'): hints[sp['tab_title']['key']] = {'place': 'tab'}
    for k in ph_keys: hints[k] = {'place': 'input'}
    for k, h in hints.items():
        h['msg'] = sp.get('hints', {}).get(k) or HMSG[h['place']]
    hint_open = sp.get('hint_open')
    if not hint_open:
        mdt = re.match(r'(\d{4})/(\d{2})/(\d{2})', MARK.sub(lambda m: m.group(1), date_raw))
        if mdt:
            d0 = datetime.date(int(mdt.group(1)), int(mdt.group(2)), int(mdt.group(3)))
            d1 = d0 + datetime.timedelta(days=((3 - d0.weekday()) % 7) or 7)
            hint_open = d1.isoformat() + 'T19:00:00+09:00'
    t = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
    js = lambda v: json.dumps(v, ensure_ascii=False)
    rep = {
        'DESC': html.escape(f"この掲示板のどこかに、{sp['noun']}が{len(keys)}個隠れています。何%見つけられる？ #かくれんぼスレ"),
        'PAGE_URL': html.escape(sp.get('page_url', '')),
        'TITLE': html.escape(sp['title']), 'TITLE_HTML': mk_html(title_raw), 'BOARD': html.escape(sp['board']), 'NOUN': html.escape(sp['noun']),
        'TOTAL': str(len(keys)), 'RESCOUNT': ('1001' if sp.get('end_1000') else str(1 + len(sp.get('replies', [])))), 'THREAD': '\n'.join(posts),
        'FOOT': html.escape(sp['foot']), 'SHARE_URL': js(sp.get('share_url', '')), 'QUOTE_URL': js(sp.get('quote_url', '')), 'NEXT': html.escape(sp.get('next_schedule', '月・金の21時')), 'KEYS': js(keys),
        'LABEL': js(sp['labels']), 'NEAR': js(sp.get('near', {})), 'GENERIC': js([sp['noun']] + sp.get('generic', [])), 'MISS': sp.get('miss_verb', 'ない'), 'LEVELS': js(sp.get('levels', {})), 'SPECIAL': js(sp.get('special', {})), 'TITLES': js(sp.get('titles', {})), 'FOLLOW_FIRST': 'true' if sp.get('follow_first') else 'false', 'SECRET': js({a: {'k': k, 'label': v['label'], 'msg': v['msg']} for k, v in sp.get('secret', {}).items() for a in [k] + v.get('alias', [])}), 'OP_NAME_JS': js(sp['op_name']),
        'OP_ID_JS': js(sp['op_id']), 'TAB_TITLE': js(sp.get('tab_title')), 'HINTS': js(hints), 'PLACEHOLDER': html.escape(MARK.sub(lambda m: m.group(1), ph_raw) if ph_raw else f"見つけた{sp['noun']}を書き込む"), 'HINT_OPEN': js(hint_open), 'OTHERS': js(others), 'LATE': js(late_info), 'STORE': js(sp['store']), 'TWIST': js(sp.get('twist')), 'SFX_TWIST': js(sfx_uri('twist.mp3')), 'SFX_POST': js(sfx_uri('post.mp3')),
    }
    for k, v in rep.items():
        t = t.replace('{{' + k + '}}', v)
    t = t.replace('let resNo = 4;', f'let resNo = {1 + len(sp.get("replies", []))};')
    assert '{{' not in t
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'index.html'), 'w', encoding='utf-8').write(t)

    # X投稿用画像のHTML
    plain = html.escape(MARK.sub(lambda m: m.group(1), body).replace('<<省略>>', ''))
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
    if sp.get('poster_style') == 'ui':
        # 検証B'/本番型: 冒頭だけ見せて、下にサイトの入力欄の絵（tools/poster_ui_sample.html と同じ見た目）
        lines = [l for l in MARK.sub(lambda m: m.group(1), body).replace('<<省略>>', '').split('\n') if l.strip()][:6]
        cnt = sp.get('counter', '個'); noun = html.escape(sp['noun'])
        poster = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body{{margin:0;font-family:"Noto Sans JP","Hiragino Kaku Gothic ProN",sans-serif}}
.c{{width:1200px;height:1200px;background:#efefef;box-sizing:border-box;padding:56px 64px;display:flex;flex-direction:column}}
.b{{font-size:26px;color:#777;border-bottom:1px solid #ccc;padding-bottom:12px}}
h1{{color:#c00;font-size:40px;line-height:1.35;margin:22px 0 14px}}
.h{{font-size:24px;color:#555}}.nm{{color:#008000;font-weight:bold}}
.t{{font-size:38px;line-height:1.75;margin:12px 0 0 24px;color:#111;position:relative;height:420px;overflow:hidden}}
.t:after{{content:"";position:absolute;left:0;right:0;bottom:0;height:200px;background:linear-gradient(rgba(239,239,239,0),#efefef)}}
.more{{text-align:center;font-size:26px;color:#888;margin:-6px 0 22px}}
.dock{{margin-top:auto;background:#fff;border-top:4px solid #c00;border-radius:18px;box-shadow:0 6px 24px rgba(0,0,0,.12);padding:28px 30px}}
.rule{{font-size:34px;font-weight:bold;color:#111;margin-bottom:20px}}.rule b{{background:#ffe14d;padding:0 8px}}
.prog{{display:flex;align-items:center;gap:18px;font-size:28px;color:#555;margin-bottom:20px}}
.bar{{flex:1;height:16px;background:#e5e5e5;border-radius:8px}}
.box{{display:flex;gap:16px}}
.in{{flex:1;height:84px;border:3px solid #bbb;border-radius:12px;font-size:32px;color:#aaa;display:flex;align-items:center;padding:0 22px}}
.btn{{width:230px;height:84px;background:#d22;color:#fff;font-size:36px;font-weight:bold;border-radius:12px;display:flex;align-items:center;justify-content:center;box-shadow:0 5px 0 #900}}
.ex{{font-size:24px;color:#7a3dbd;margin-top:16px}}
</style></head><body><div class="c" id="c">
<div class="b">■ かくれんぼスレ ■ {html.escape(sp['board'])}</div>
<h1>{html.escape(sp['title'])}</h1>
<div class="h">1 名前：<span class="nm">{nm}</span> {sp['op_date']}</div>
<div class="t">{'<br>'.join(html.escape(l) for l in lines)}</div>
<div class="more">▼ 続きはリンク先のスレで</div>
<div class="dock">
<div class="rule">この掲示板のどこかに、<b>{noun}が{len(keys)}{cnt}</b>かくれている。</div>
<div class="prog"><span>0 / {len(keys)}（0%）</span><div class="bar"></div><span>一覧</span></div>
<div class="box"><div class="in">見つけた{noun}を書き込む</div><div class="btn">書き込む</div></div>
{'<div class="ex">※うち1つは、ひとひねりある「高難度隠し」</div>' if sp.get('special') else ''}
</div></div></body></html>'''
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
<div class="q">この掲示板のどこかに、<span>{html.escape(sp['noun'])}が{len(keys)}個</span>隠れています。</div>
</div></body></html>'''
    open(os.path.join(outdir, 'og.html'), 'w', encoding='utf-8').write(og)
    print('generated', outdir, len(keys), 'keys')

main()
