# かくれんぼスレ（gaasuu8910.github.io/kakurenbo/（独自ドメイン準備中。将来 hownever.com/kakurenbo/））

2ちゃんねる風の書き込みに、あるジャンルの言葉が20個かくれている謎解きシリーズ。
X：[@gaasuuquestion](https://x.com/gaasuuquestion)　タグ：#かくれんぼスレ

## 構成
- `threads/<slug>/` … 1スレ分のデータ
  - `body.txt` … >>1本文。隠し語は `{表示|読み}` でマーク（例：`想{像|ぞう}以上に`）
  - `spec.json` … タイトル・板名・ID・正解（KEYS/LABEL）・惜しい返答（near）・特別返答（special）など
  - `words.txt` … そのジャンルの広い語彙リスト（意図しない語の混入チェック用）
  - `post.png` … X投稿用の画像（自動生成）
- `threads.json` … 公開するスレの一覧（番号・slug・日付）
- `tools/` … 生成・検査ツール
- `docs/` … 公開されるサイト（自動生成。GitHub Pages の公開元）

## 作り方のルール
- 隠す言葉は3文字以上を基本にする（2文字は隠しやすい分、芸術点が低い）。長い言葉ほどよい
- 1スレに1つ「高難度隠し」を入れる（縦読み・IDのローマ字・漢字の中の漢字・斜め読みなど）。spec.json の special に `{"読み": "発見時の>>1のセリフ"}` を書くと、発見時に特別な演出が出る
- spec.json の levels に、隠し語ごとのレベルを書く（一覧ボタンでレベル別に表示される）
  - レベル1：単語の中に、そのまま読める（例：飽きた→秋田、ヘビーユーザー→ヘビ）
  - レベル2：ひらがな（カナ）で単語をまたぐ（例：まあじっくり→アジ、おにぎりとちぎりパン→栃木）
  - レベル3：漢字で単語をまたぐ、または漢字の読みを分ける（例：結構近い→高知）
  - EX：special に入れたもの（高難度隠し）
- 名字や地名など、同じ音の固有名詞をそのまま当てるのは禁止（例：外山→富山）。人名を使うなら単語をまたぐ形に（例：弟のヒロシまで→広島）
- >>1は日本語として自然な2ちゃんねるの書き込みであること（tools/checker_prompt.md で精査）

## 新しいスレを足す手順
1. `threads/<slug>/` に `body.txt`・`spec.json`・`words.txt` を作る
2. 読みの検査：`python3 tools/check_hidden.py threads/<slug>/body.txt threads/<slug>/words.txt`
   - KEYS が全部入っていて（MISSING なし）、EXTRA（意図しない語）がないこと
3. 日本語チェック：`tools/checker_prompt.md` の指示で、書いた人とは別の目で全行を精査（NG 0 まで）
4. `threads.json` に追加して `python3 tools/build_site.py`（全スレの自動テストつき）
5. `main` に push すると GitHub Pages で公開される

必要なもの：`pip install --break-system-packages pykakasi playwright`、Chrome（または `playwright install chromium`）
