# ぼうけんのしょ の更新

## 窓の画像

`assets/*.svg` は `tools/build_svg.py` が生成します。文言を変えるときは、このスクリプトの中身（`SPELLS` / `PARTY` / `STRATEGY` と各関数の文字列）を直してから生成し直します。

```bash
python3 -m pip install fonttools
curl -fsSL -o /tmp/DotGothic16-Regular.ttf \
  https://github.com/google/fonts/raw/main/ofl/dotgothic16/DotGothic16-Regular.ttf
python3 tools/build_svg.py /tmp/DotGothic16-Regular.ttf
```

- 文字は DotGothic16（SIL Open Font License 1.1）の字形を図形に変換して埋め込みます。フォントファイル自体はリポジトリに置きません。
- フォントに無い文字を使うと、スクリプトはその文字を表示して止まります。`▶` だけは図形で描いています。

## ぼうけんの ちず と きろく

`adventure.svg` は `.github/workflows/adventure.yml` が毎日 0:00（日本時間）に作り直し、`output` ブランチに置きます。手元で試すときは次のとおりです。

```bash
gh api graphql -F query=@tools/calendar.graphql -f login=oyster-dev > /tmp/calendar.json
cd tools && python3 adventure.py /tmp/DotGothic16-Regular.ttf /tmp/calendar.json /tmp/out
```

- 1 日を 1 マスの地形にします。活動の無い日は うみ、多い日ほど そうげん → もり → やま、いちばん活動した日は しろ です。
- ゆうしゃ は活動した日を日付順に歩き、最後は今日のマスで止まります。
- レベルは 1 年分のコントリビューション数を経験値にして計算します（必要経験値は 5 ×（レベル − 1）²）。
- 手元の `gh` はご本人の権限で取得するため、公開プロフィールより多い件数が返ることがあります。手元で作った `adventure.svg` はコミットしないでください。
