"""隠れ言葉チェッカー: body.txt の {表示|読み} マークアップを検証し、
意図しない言葉が読みに混ざっていないかを語彙リストで調べる。
usage: python3 check_hidden.py body.txt wordlist.txt [fix=from:to ...]"""
import re, sys, unicodedata
import pykakasi

kks = pykakasi.kakasi()
MARK = re.compile(r'\{([^|{}]+)\|([^{}]+)\}')

def to_hira(s):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)

def norm(s):
    s = unicodedata.normalize('NFKC', s)
    s = re.sub(r'[\s、。，,．.！!？?「」『』【】“”"・〜～ー…（）()]', '', s)
    return to_hira(s)

def reading(s):
    return norm(''.join(x['hira'] for x in kks.convert(s)))

def main():
    body = open(sys.argv[1], encoding='utf-8').read()
    words = [w.strip() for w in open(sys.argv[2], encoding='utf-8').read().split() if w.strip()]
    fixes = [a.split('=', 1)[1].split(':') for a in sys.argv[3:] if a.startswith('fix=')]
    plain = MARK.sub(lambda m: m.group(1), body)
    marks = MARK.findall(body)
    r = reading(plain)
    for a, b in fixes:
        r = r.replace(a, b)
    print('READING:', r, '\n')
    ok = True
    # 1) 各マークの読みが、表示テキストの読みの中に入っているか
    for vis, key in marks:
        vr = reading(vis)
        for a, b in fixes:
            vr = vr.replace(a, b)
        if key not in r:
            print('NG  not in reading:', key, f'({vis})'); ok = False
    keys = sorted(set(k for _, k in marks))
    # 2) 語彙リストとの照合
    found = {w: r.count(w) for w in words if w in r}
    extra = {w: c for w, c in found.items() if w not in keys}
    missing = [k for k in keys if k not in r]
    print('KEYS', len(keys), keys)
    print('EXTRA (意図外):', extra)
    print('MISSING:', missing)
    # キーが他のキーの一部か（例: みる ⊂ みるがい）
    print('OK' if ok and not missing else 'CHECK FAILED')

main()
