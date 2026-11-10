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
    "lamp": .11, "ac": .10, "clock": .085, "street": .02, "cat": .18,
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

# предметы в покое не светятся: «active» только пока источник звучит;
# после клика телефон моргает диодами и гаснет, у принтера выезжает лист
sub('function On(v,r){return(v.confirmedUntil[r]??0)>v.visualTime?r==="printer"?"after click":"Default":"active"}',
    'function On(v,r){const c=(v.confirmedUntil[r]??0)-v.visualTime;'
    'return c>0?r==="phone"&&Math.floor(c/.11)%2===0?"active":"Default"'
    ':v.active.has(r)?"active":"Default"}')
sub('.map(([q])=>q).join(",")}`',
    '.map(([q])=>q).join(",")}|${[...O.active].join()}|'
    '${Object.values(O.confirmedUntil).some(q=>q>O.visualTime)?Math.floor(O.visualTime/.055):0}`')
# кот машет лапой, пока стучит (ТЗ, раздел 14)
sub('${O.inArrival?"arrival":""} ', '${O.inArrival?"arrival":""} ${O.active.has("cat")?"cat-on":""} ')

# игра доступна слою анимаций сразу (часы, шкала), а не только после клика
sub("r(new O7(Math.random,q))", "r(window.__fxGame=new O7(Math.random,q))")
# пауза, пока сцена не дорисуется: время игры стоит (см. fx.js)
sub("Re.tick(zt)", "Re.tick(window.__hold?0:zt)")
# онбординг идёт вдвое спокойнее
sub("this.introElapsed=Math.min(we.complete,this.introElapsed+d)",
    "this.introElapsed=Math.min(we.complete,this.introElapsed+d*.5)")
# время суток: все четыре вида за окном лежат слоями и плавно перетекают
sub('children:r==="день"?s.jsx(Px,{}):r==="вечер"?s.jsx(ch,{}):r==="поздний вечер"?s.jsx(xh,{}):s.jsx(ab,{className:"relative size-full"})})',
    'children:[["утро",s.jsx(ab,{className:"relative size-full"})],["день",s.jsx(Px,{})],["вечер",s.jsx(ch,{})],["поздний вечер",s.jsx(xh,{})]]'
    '.map(([k,el],i)=>s.jsx("div",{className:"fx-sky"+(k===r?" fx-on":""),children:el},i))})')
# освещение кабинета — так же, слоями
sub('s.jsx(zx,{propValue:r,className:"-translate-x-1/2 -translate-y-1/2 absolute h-[402px] left-1/2 mix-blend-soft-light opacity-40 overflow-clip top-1/2 w-[874px]"})',
    '["утро","день","вечер","поздний вечер"].map((k,i)=>s.jsx(zx,{propValue:k,className:"-translate-x-1/2 -translate-y-1/2 absolute h-[402px] left-1/2 mix-blend-soft-light overflow-clip top-1/2 w-[874px] fx-light"+(k===r?(i===3?" fx-on-80":" fx-on-40"):"")},"l"+i))')

# принтер: после гашения лист плавно выезжает в лоток и остаётся там
sub('this.confirmedUntil[r]=this.visualTime+(r==="printer"?1.2:.7)',
    'this.confirmedUntil[r]=this.visualTime+(r==="printer"?1.2:.7),r==="printer"&&(this.printed=(this.printed||0)+1)')
sub('children:s.jsx(gx,{state:On(o,"printer"),className:"relative size-full"})',
    'children:[s.jsx(gx,{state:On(o,"printer"),className:"relative size-full"},"p"),'
    'o.printed>0&&s.jsx("div",{className:"fx-sheet",children:s.jsx("img",{alt:"",src:xx})},"s"+o.printed)]')
# мойщик: сначала пишет «БЕГИТЕ ГЛУПЦЫ», потом моет; зона клика — и скребок, и надпись
sub('O.found.has("washer")&&s.jsxs("div",{className:"window-message",',
    '(O.found.has("washer")||O.washerVisible)&&s.jsxs("div",{className:"window-message"+'
    '(O.found.has("washer")?" kept":O.elapsed<100?" writing-pass":" writing-stay"),')
sub('{id:"washer",label:"Мойщик окон",x:8,y:183,w:60,h:132}',
    '{id:"washer",label:"Мойщик окон",x:0,y:150,w:72,h:170}')
# в окне находки надпись читается нормально, не зеркально
sub('"-scale-x-100 flex-none h-[hypot(9.70461cqw,72.1583cqh)] rotate-[-11.51deg]',
    '"flex-none h-[hypot(9.70461cqw,72.1583cqh)] rotate-[11.51deg]')

css += open(os.path.join(ROOT, "tools", "fx.css"), encoding="utf8").read()
open(os.path.join(A, "game.js"), "w", encoding="utf8").write(js)
open(os.path.join(A, "game.css"), "w", encoding="utf8").write(css)
print("patched: docs/assets/game.js, game.css")
