# ぼうけんのしょ の更新

窓の画像（`assets/*.svg`）は `tools/build_svg.py` が生成します。文言を変えるときは、このスクリプトの中身（`SPELLS` / `PARTY` / `STRATEGY` と各関数の文字列）を直してから生成し直します。

```bash
python3 -m pip install fonttools
curl -fsSL -o /tmp/DotGothic16-Regular.ttf \
  https://github.com/google/fonts/raw/main/ofl/dotgothic16/DotGothic16-Regular.ttf
python3 tools/build_svg.py /tmp/DotGothic16-Regular.ttf
```

- 文字は DotGothic16（SIL Open Font License 1.1）の字形を図形に変換して埋め込みます。フォントファイル自体はリポジトリに置きません。
- フォントに無い文字を使うと、スクリプトはその文字を表示して止まります。`▶` だけは図形で描いています。
- 草の蛇（`snake-*.svg`）は `.github/workflows/snake.yml` が毎日 0:00（日本時間）に作り直し、`output` ブランチに置きます。
