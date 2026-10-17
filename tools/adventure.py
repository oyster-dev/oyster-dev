#!/usr/bin/env python3
"""草（コントリビューションのカレンダー）から「ぼうけんの ちず」と「ぼうけんの きろく」を描く。

1 日を 1 マスの地形にする。活動が無い日は うみ、多い日ほど そうげん → もり → やま、
いちばん活動した日は しろ。ゆうしゃ は活動した日を日付順に歩き、最後は今日のマスに立つ。

使い方:
    gh api graphql -F query=@tools/calendar.graphql -f login=<ユーザー名> > calendar.json
    python3 tools/adventure.py <DotGothic16-Regular.ttf> calendar.json <出力先ディレクトリ>
"""
import json
import math
import sys
from datetime import date
from pathlib import Path

from build_svg import DIM, GOLD, WHITE, W, Canvas, Font

TILE = 15
PX = 3
GRASS = "#3c9a40"

# 5x5 のドット絵。"." は下地の色のまま
SPRITES = {
    "sea": ("#1f4aa8", {"w": "#7fb0ff"}, [".....", ".w...", ".....", "...w.", "....."]),
    "grass": (GRASS, {"g": "#7fd36a"}, [".....", ".g...", "...g.", ".....", "g...."]),
    "forest": (GRASS, {"t": "#1d5e2b", "b": "#7a4a1e"}, ["..t..", ".ttt.", "ttttt", "..b..", "....."]),
    "mountain": (GRASS, {"m": "#9a7442", "d": "#6e5230"}, ["..m..", ".mmd.", "mmmdd", "mmmmd", "....."]),
    "snow": (GRASS, {"s": "#f4f4f4", "m": "#9a7442", "d": "#6e5230"}, ["..s..", ".ssd.", "mmmdd", "mmmmd", "....."]),
    "castle": (GRASS, {"c": "#d8d8e0", "r": "#d23c3c", "d": "#5a5a6a"}, ["..r..", "c.c.c", "ccccc", "ccdcc", "ccdcc"]),
}
HERO = (
    {"H": "#e8c040", "F": "#f2c79b", "B": "#2d4bd8", "S": "#ffffff", "L": "#6b3b1e"},
    [".HH..", ".FF.S", "BBBBS", ".BB..", ".L.L."],
)
TERRAIN = {
    "NONE": "sea",
    "FIRST_QUARTILE": "grass",
    "SECOND_QUARTILE": "forest",
    "THIRD_QUARTILE": "mountain",
    "FOURTH_QUARTILE": "snow",
}
LEGEND = [("sea", "うみ"), ("grass", "そうげん"), ("forest", "もり"), ("mountain", "やま"), ("castle", "しろ")]
STEP = 0.15  # ゆうしゃ が 1 マス進む秒数
REST = 2.4  # 今日のマスで止まる秒数


def pixels(colors, rows):
    return "".join(
        f'<rect x="{x * PX}" y="{y * PX}" width="{PX}" height="{PX}" fill="{colors[ch]}"/>'
        for y, row in enumerate(rows)
        for x, ch in enumerate(row)
        if ch != "."
    )


def sprite_defs():
    defs = []
    for name, (base, colors, rows) in SPRITES.items():
        defs.append(
            f'<g id="t-{name}"><rect width="{TILE}" height="{TILE}" fill="{base}"/>{pixels(colors, rows)}</g>'
        )
    defs.append(f'<g id="hero">{pixels(*HERO)}</g>')
    return defs


def level(exp):
    """必要経験値は 5 × (レベル − 1)²。"""
    lv = min(99, 1 + math.isqrt(exp // 5))
    if lv == 99:
        return lv, None, 1.0
    low, high = 5 * (lv - 1) ** 2, 5 * lv ** 2
    return lv, high - exp, (exp - low) / (high - low)


def adventure(font, calendar):
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]
    days = [(i, j, d) for i, w in enumerate(weeks) for j, d in enumerate(w["contributionDays"])]
    traveled = [cell for cell in days if cell[2]["contributionCount"] > 0]
    best = max(traveled, key=lambda c: (c[2]["contributionCount"], c[2]["date"]), default=None)
    lv, need, progress = level(total)

    c = Canvas(font, 424, f"ぼうけんの ちず と きろく: この 1ねんで {len(traveled)}にち たびをした。レベル {lv}")
    c.defs.extend(sprite_defs())

    c.window(6, 22, W - 12, 190, "ぼうけんの ちず")
    x0 = 6 + (W - 12 - len(weeks) * TILE) // 2
    y0 = 56

    def at(i, j):
        return x0 + i * TILE, y0 + j * TILE

    for i, j, d in days:
        x, y = at(i, j)
        tile = "castle" if best and (i, j) == best[:2] else TERRAIN[d["contributionLevel"]]
        c.raw(f'<use href="#t-{tile}" x="{x}" y="{y}"/>')

    today = at(*days[-1][:2])
    route = [at(i, j) for i, j, _ in traveled] + [today] * math.ceil(REST / STEP)
    values = ";".join(f"{x} {y}" for x, y in route)
    c.raw(
        f'<g transform="translate({today[0]} {today[1]})"><use href="#hero"/>'
        f'<animateTransform attributeName="transform" type="translate" values="{values}" '
        f'dur="{len(route) * STEP:.2f}s" calcMode="discrete" repeatCount="indefinite"/></g>'
    )

    x = x0
    for tile, label in LEGEND:
        c.raw(f'<use href="#t-{tile}" x="{x}" y="181"/>')
        x = c.text(label, x + TILE + 6, 194, 14, DIM) + 22

    c.window(6, 236, W - 12, 180, "ぼうけんの きろく")
    if traveled:
        c.text(f"Hiroki は この 1ねんで {len(traveled)}にち たびをした！", 40, 290, 22)
    else:
        c.text("Hiroki は まだ たびに でていない。", 40, 290, 22)

    x = c.text(f"レベル {lv}", 40, 328, 22) + 16
    for k in range(10):
        filled = k < round(progress * 10)
        c.raw(
            f'<rect x="{x + k * 17}" y="311" width="14" height="18" '
            f'fill="{GOLD if filled else "none"}" stroke="{GOLD}" stroke-width="2"/>'
        )
    rest = "さいだい レベル" if need is None else f"つぎの レベルまで あと {need}"
    c.text(rest, x + 10 * 17 + 14, 328, 18)

    if best:
        m, d = (int(v) for v in best[2]["date"].split("-")[1:])
        c.text(f"いちばん たたかった ひ  {m}がつ{d}にち（{best[2]['contributionCount']}かい）", 40, 366, 22)
    c.text(f"けいけんち {total} = この 1ねんの コントリビューション すう", 40, 398, 16, DIM)
    return c


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    font = Font(sys.argv[1])
    data = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    path = out / "adventure.svg"
    path.write_text(adventure(font, calendar).svg(), encoding="utf-8")
    print(f"{path}  {path.stat().st_size // 1024} KB  ({date.today()})")


if __name__ == "__main__":
    main()
