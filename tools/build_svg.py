#!/usr/bin/env python3
"""ぼうけんのしょ の SVG を assets/ に生成する。

README に貼った SVG は外部フォントを読み込めないため、DotGothic16 の字形を path に変換して埋め込む。

使い方:
    pip install fonttools
    curl -fsSL -o /tmp/DotGothic16-Regular.ttf \
      https://github.com/google/fonts/raw/main/ofl/dotgothic16/DotGothic16-Regular.ttf
    python3 tools/build_svg.py /tmp/DotGothic16-Regular.ttf
"""
import re
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

OUT = Path(__file__).resolve().parent.parent / "assets"
W = 840

WHITE = "#ffffff"
DIM = "#9fb3c8"
GOLD = "#ffe27a"
AI = "#7cc2e6"

STYLE = """
.c{opacity:0;animation:show .01s steps(1) forwards}
.blink{animation:blink 1s steps(1) infinite}
.lvup{animation:lvup 1.6s steps(1) 1.2s 1 both}
@keyframes show{to{opacity:1}}
@keyframes blink{50%{opacity:0}}
@keyframes lvup{0%,25%,50%,75%{opacity:1}12%,37%,62%{opacity:.15}}
@media (prefers-reduced-motion:reduce){.c{opacity:1;animation:none}.blink,.lvup{animation:none}}
"""


class Font:
    def __init__(self, path):
        self.font = TTFont(path)
        self.cmap = self.font.getBestCmap()
        self.glyphs = self.font.getGlyphSet()
        self.hmtx = self.font["hmtx"]
        self.upm = self.font["head"].unitsPerEm
        self.paths = {}

    def name(self, ch):
        if ord(ch) not in self.cmap:
            raise SystemExit(f"フォントに無い文字です: {ch!r}")
        return self.cmap[ord(ch)]

    def path(self, name):
        if name not in self.paths:
            pen = SVGPathPen(self.glyphs)
            self.glyphs[name].draw(pen)
            self.paths[name] = pen.getCommands()
        return self.paths[name]

    def width(self, text, size):
        return sum(self.advance(ch) for ch in text) * size / self.upm

    def advance(self, ch):
        if ch == "▶":
            return self.upm
        return self.hmtx[self.name(ch)][0]


class Canvas:
    def __init__(self, font, height, label):
        self.font = font
        self.height = height
        self.label = label
        self.used = set()
        self.body = []

    def text(self, s, x, y, size=24, fill=WHITE, start=None, step=0.07, cls=""):
        """y はベースライン。start を渡すと 1 文字ずつ表示する。"""
        sc = size / self.font.upm
        parts = []
        for i, ch in enumerate(s):
            anim = ""
            if start is not None:
                anim = f' class="c" style="animation-delay:{start + i * step:.2f}s"'
            if ch == "▶":
                parts.append(self._triangle(x, y, size, anim))
            elif not ch.isspace():
                name = self.font.name(ch)
                self.used.add(name)
                parts.append(
                    f'<use href="#{gid(name)}" transform="translate({x:.1f} {y:.1f}) '
                    f'scale({sc:.4f} {-sc:.4f})"{anim}/>'
                )
            x += self.font.advance(ch) * sc
        klass = f' class="{cls}"' if cls else ""
        self.body.append(f'<g fill="{fill}"{klass}>{"".join(parts)}</g>')
        return x

    def _triangle(self, x, y, size, anim):
        top, mid, bottom = y - size * 0.78, y - size * 0.4, y - size * 0.02
        right = x + size * 0.62
        return f'<polygon points="{x:.1f},{top:.1f} {right:.1f},{mid:.1f} {x:.1f},{bottom:.1f}"{anim}/>'

    def window(self, x, y, w, h, title=None, title_size=20):
        # 外側の黒い縁で、ライトモードの白背景でも白線が溶けないようにする
        self.body.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#000"/>'
            f'<rect x="{x + 6}" y="{y + 6}" width="{w - 12}" height="{h - 12}" rx="9" '
            f'fill="none" stroke="#fff" stroke-width="4"/>'
        )
        if title:
            tw = self.font.width(title, title_size)
            tx = x + (w - tw) / 2
            # 見出しは上辺の白線に重ねる
            self.body.append(
                f'<rect x="{tx - 8:.1f}" y="{y - 6}" width="{tw + 16:.1f}" height="24" fill="#000"/>'
            )
            self.text(title, tx, y + 6 + title_size * 0.36, title_size, WHITE)

    def raw(self, s):
        self.body.append(s)

    def svg(self):
        defs = "".join(
            f'<path id="{gid(n)}" d="{self.font.path(n)}"/>' for n in sorted(self.used)
        )
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.height}" '
            f'width="{W}" height="{self.height}" role="img" aria-label="{self.label}">'
            f"<title>{self.label}</title><style>{STYLE}</style><defs>{defs}</defs>"
            f'{"".join(self.body)}</svg>\n'
        )


def gid(name):
    return "g" + re.sub(r"[^A-Za-z0-9_-]", "_", name)


def message(font):
    c = Canvas(font, 150, "Hiroki が あらわれた！ しつじ セバスチャン が なかまに くわわった！")
    c.window(6, 6, W - 12, 138)
    c.text("Hiroki が あらわれた！", 44, 64, 26, start=0.3)
    c.text("しつじ セバスチャン が なかまに くわわった！", 44, 110, 26, start=1.9)
    c.raw('<g class="c" style="animation-delay:3.7s"><g class="blink">')
    c.text("▼", W - 64, 132, 20)
    c.raw("</g></g>")
    return c


def status(font):
    c = Canvas(font, 250, "コマンド: つよさ じゅもん なかま さくせん。つよさ: なまえ Hiroki、しょくぎょう あそびにん から けんじゃ、とくぎ しくみで らくをする、さくせん らくして たのしむ")
    c.window(6, 22, 230, 222, "コマンド")
    for i, item in enumerate(["つよさ", "じゅもん", "なかま", "さくせん"]):
        c.text(item, 62, 84 + i * 44, 24)
    c.raw('<g class="blink">')
    c.text("▶", 32, 84, 24)
    c.raw("</g>")

    c.window(252, 22, W - 258, 222, "つよさ")
    rows = [
        ("なまえ", "Hiroki"),
        ("しょくぎょう", None),
        ("とくぎ", "しくみで らくをする"),
        ("さくせん", "らくして たのしむ"),
    ]
    for i, (label, value) in enumerate(rows):
        y = 84 + i * 44
        c.text(label, 284, y, 22, DIM)
        if value:
            c.text(value, 448, y, 22)
        else:
            x = c.text("あそびにん → ", 448, y, 22)
            c.text("けんじゃ", x, y, 22, GOLD, cls="lvup")
    return c


SPELLS = [
    ("ゴー", "Go", "バックエンドを くみたてる"),
    ("ポスグレ", "PostgreSQL", "データを かたく まもる"),
    ("ドッカー", "Docker", "かんきょうを はこに とじこめる"),
    ("テラフォーム", "Terraform", "となえるのは ほんにんのみ"),
    ("アクションズ", "GitHub Actions", "ねている あいだも はたらかせる"),
    ("エージェント", "AI", "Claude Code / Codex / Cursor"),
]


def spells(font):
    rows = (len(SPELLS) + 1) // 2
    h = 22 + 40 + rows * 78
    label = "じゅもん: " + "、".join(f"{n}（{en}）{d}" for n, en, d in SPELLS)
    c = Canvas(font, h, label)
    c.window(6, 22, W - 12, h - 22, "じゅもん")
    for i, (name, en, desc) in enumerate(SPELLS):
        x = 44 + (i % 2) * 400
        y = 86 + (i // 2) * 78
        end = c.text(name, x, y, 24)
        c.text(en, end + 12, y, 16, AI)
        c.text(desc, x, y + 30, 18, DIM)
    return c


PARTY = [
    ("Hiroki", "けんじゃ", ["らくして", "たのしむ"]),
    ("セバスチャン", "しつじ", ["おまかせ", "くださいませ"]),
    ("Codex", "まほうつかい", ["べつの めで", "みなおす"]),
    ("Cursor", "せんし", ["エディタで", "ともに たたかう"]),
]


def party(font):
    label = "なかま: " + "、".join(f"{n}（{job}）{''.join(words)}" for n, job, words in PARTY)
    c = Canvas(font, 200, label)
    gap = 12
    w = (W - 12 - gap * 3) / 4
    for i, (name, job, words) in enumerate(PARTY):
        x = 6 + i * (w + gap)
        c.window(x, 22, w, 172, name)
        c.text("しょくぎょう", x + 22, 74, 16, DIM)
        c.text(job, x + 22, 104, 22, GOLD if i == 0 else WHITE)
        for j, line in enumerate(words):
            c.text(line, x + 22, 142 + j * 26, 18)
    return c


STRATEGY = [
    ("しくみで らくをする", "おなじ しっぱいを にどと しない"),
    ("なかまを つよくする", "くふうを みんなの ざいさんに"),
    ("らくして たのしむ", "それが けんじゃへの みち"),
]


def strategy(font):
    label = "さくせん: " + "、".join(f"{a}（{b}）" for a, b in STRATEGY)
    c = Canvas(font, 200, label)
    c.window(6, 22, W - 12, 172, "さくせん")
    for i, (name, desc) in enumerate(STRATEGY):
        y = 84 + i * 44
        c.text(name, 72, y, 24)
        c.text(desc, 370, y, 18, DIM)
    c.raw('<g class="blink">')
    c.text("▶", 40, 84, 24)
    c.raw("</g>")
    return c


def main():
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    font = Font(sys.argv[1])
    OUT.mkdir(exist_ok=True)
    for build in (message, status, spells, party, strategy):
        path = OUT / f"{build.__name__}.svg"
        path.write_text(build(font).svg(), encoding="utf-8")
        print(f"{path.relative_to(OUT.parent)}  {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
