#!/usr/bin/env python3
"""Патчит исходную (минифицированную) сборку из tools/vendor и кладёт результат в docs/assets.

Запуск: python3 tools/patch_bundle.py   (после tools/build_sounds.py)
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(ROOT, "tools", "vendor")
A = os.path.join(ROOT, "docs", "assets")
js = open(os.path.join(V, "index.js"), encoding="utf8").read()
css = open(os.path.join(V, "index.css"), encoding="utf8").read()


def sub(old, new, count=1):
    global js
    assert js.count(old) == count, (old[:60], js.count(old))
    js = js.replace(old, new)


# --- звук: новые файлы, громкости и бесшовные петли ---
loops = json.load(open(os.path.join(ROOT, "docs", "audio", "loops.json")))
gains = {
    "phone": .42, "printer": .40, "keyboard": 1.0, "mobile": .5, "pc": .34,
    "lamp": .085, "ac": .10, "clock": .085, "street": .02, "cat": .18,
    "room": .01, "pulse": .08,
    "sip-1": .3, "sip-2": .3, "empty-cup": .28, "break": .34,
    "pop-1": .3, "pop-2": .3, "pop-3": .3, "pop-4": .3, "pop-5": .3, "pop-6": .3,
    "switch": .4, "step-1": .2, "step-2": .2, "chair": .21,
    "success": .3, "touch": .03, "miss": .03, "button": .25, "result": .35,
}
table = ",".join(
    '"%s":{file:"./audio/%s.mp3",gain:%s%s}' % (
        k, k, g, (",loop:%s" % loops["length"][k]) if k in loops["length"] else "")
    for k, g in gains.items())
m = re.search(r"const oc=\{.*?\}\},Ss=", js)
assert m
js = js[:m.start()] + "const oc={" + table + "},Ss=" + js[m.end():]
at = loops["loopAt"]
sub("A.loop=!0,", "A.loop=!0,o.loop&&(A.loopStart=%s,A.loopEnd=%s+o.loop)," % (at, at))
sub("stop:U}),A.start()}", "stop:U}),A.start(0,o.loop?%s:0)}" % at)

# --- анимации ---
# хук на каждый клик (кот, кружка, пупырка, вилка, окно, часы) — см. fx.js
sub('const ee=O.act(q);ee!=="ignored"&&(',
    'const ee=O.act(q);ee!=="ignored"&&(window.__fx&&window.__fx(q,ee,O),')
# стадия стресса — классом на комнате (виньетка, отклик персонажа)
sub("re=O?`period-${ue} ", 're=O?`mood-${O.mood.replace(" ","-")} period-${ue} ')
# срыв: полноценная анимация вместо 0.65 с
sub("this.endingElapsed>=.65", "this.endingElapsed>=1.55")
# окно находки улетает перед закрытием
sub("L=()=>{Be(null),O?.closeEgg(),S(q=>q+1)}",
    "L=()=>{const c=()=>{Be(null),O?.closeEgg(),S(q=>q+1)};window.__eggOut?window.__eggOut(c):c()}")
# мойщик: проезд в обед / возврат в 17:00
sub('"data-object":"washer",className:"absolute h-[147.635px] left-[-37px] top-[162px] w-[100.402px]"',
    '"data-object":"washer",className:"absolute h-[147.635px] left-[-37px] top-[162px] w-[100.402px] "+(o.elapsed<100?"washer-pass":"washer-stay")')

css += open(os.path.join(ROOT, "tools", "fx.css"), encoding="utf8").read()
open(os.path.join(A, "game.js"), "w", encoding="utf8").write(js)
open(os.path.join(A, "game.css"), "w", encoding="utf8").write(css)
print("patched: docs/assets/game.js, game.css")
