#!/usr/bin/env python3
"""Собирает игровые звуки из записей BigSoundBank (лицензия CC0).

Запуск:  python3 tools/build_sounds.py [папка_с_исходниками]
Нужны ffmpeg и numpy. Исходники скачиваются с bigsoundbank.com, если их нет.
Результат: docs/audio/*.mp3 и docs/audio/loops.json (длины бесшовных петель).

Петли записаны с запасом: 0.1 с вступления + период L + 0.25 с хвоста,
внутри всё периодично. Игра крутит участок [0.15; 0.15 + L], поэтому
задержка mp3-декодера шва не даёт.
"""
import json
import os
import subprocess
import sys

import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "audio")
RAW = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", ".sound-cache")
LEAD, TAIL, LOOP_AT = 0.10, 0.25, 0.15
loops = {}
rng = np.random.default_rng(7)


def src(sid):
    path = os.path.join(RAW, f"{sid}.mp3")
    if not os.path.exists(path) or os.path.getsize(path) < 1000:
        os.makedirs(RAW, exist_ok=True)
        subprocess.run(
            ["curl", "-sS", "-m", "180", "-A", "Mozilla/5.0", "-o", path,
             f"https://bigsoundbank.com/UPLOAD/mp3/{sid}.mp3"], check=True)
    return path


def load(sid, af=None):
    cmd = ["ffmpeg", "-v", "error", "-i", src(sid)]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def n(sec):
    return int(round(sec * SR))


def cut(x, a, b):
    return x[n(a):n(b)].copy()


def fade(x, fin=0.004, fout=0.02):
    x = x.copy()
    a, b = min(n(fin), len(x) // 2), min(n(fout), len(x) // 2)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b) ** 2
    return x


def env(x, win=0.005):
    w = n(win)
    m = len(x) // w
    return np.sqrt((x[:m * w].reshape(m, w) ** 2).mean(axis=1)), win


def onsets(x, rel_db=-18, gap=0.15):
    """Начала событий: огибающая поднялась выше порога после паузы gap."""
    e, win = env(x)
    thr = e.max() * 10 ** (rel_db / 20)
    out, quiet = [], 10 ** 9
    for i, v in enumerate(e):
        if v > thr:
            if quiet * win >= gap:
                out.append(max(0.0, i * win - 0.006))
            quiet = 0
        else:
            quiet += 1
    return out


def rms_active(x):
    e, _ = env(x, 0.05)
    act = e[e > e.max() * 0.1]
    return float(np.sqrt((act ** 2).mean()))


def norm(x, rms_db=None, peak=None):
    if rms_db is not None:
        x = x * (10 ** (rms_db / 20) / (rms_active(x) + 1e-12))
        top = np.abs(x).max()
        if top > 0.8:
            x = np.tanh(x / top * 1.6) / np.tanh(1.6) * 0.8
    if peak is not None:
        x = x * (peak / (np.abs(x).max() + 1e-12))
    return x


def band(x, lo=None, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    g = np.ones_like(f)
    if lo:
        g *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1e-6)) ** 6)
    if hi:
        g *= 1 / np.sqrt(1 + (f / hi) ** 6)
    return np.fft.irfft(X * g, len(x))


def seamless(seg, L, xf):
    """Периодичное ядро длиной L: хвост вкроссфейжен в начало."""
    l, k = n(L), n(xf)
    core = seg[:l].copy()
    t = np.linspace(0, np.pi / 2, k)
    core[:k] = seg[:k] * np.sin(t) + seg[l:l + k] * np.cos(t)
    return core


def place(L, events):
    """Тихая петля длиной L с событиями [(t, samples)]."""
    core = np.zeros(n(L))
    for t, s in events:
        i = n(t)
        s = s[:len(core) - i]
        core[i:i + len(s)] += s
    return core


def encode(name, x, kbps):
    os.makedirs(OUT, exist_ok=True)
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "1",
         "-i", "-", "-codec:a", "libmp3lame", "-b:a", f"{kbps}k",
         os.path.join(OUT, name + ".mp3")], input=pcm, check=True)


def loop(name, core, kbps=112):
    loops[name] = round(len(core) / SR, 4)
    core = np.roll(core, n(0.12))  # события не попадают на точку склейки
    encode(name, np.concatenate([core[-n(LEAD):], core, core[:n(TAIL)]]), kbps)
    print(f"loop {name:10s} L={loops[name]:.2f}s rms={20 * np.log10(rms_active(core)):.1f}dB")


def shot(name, x, kbps=128):
    encode(name, np.concatenate([x, np.zeros(n(0.03))]), kbps)
    print(f"shot {name:10s} {len(x) / SR:.2f}s peak={np.abs(x).max():.2f}")


def tone(freqs, dur, tau):
    t = np.arange(n(dur)) / SR
    y = sum(a * np.sin(2 * np.pi * f * t) for f, a in freqs)
    return fade(y * np.exp(-t / tau), 0.002, 0.01)


# ---------- основные источники ----------

# Телефон: настоящий звонок стационарного аппарата, пауза сокращена до 1 с.
x = load("0063", "highpass=f=250")
ring_at = onsets(x, -20, 1.0)[1]
ring = fade(cut(x, ring_at, ring_at + 1.72), 0.003, 0.08)
loop("phone", norm(place(2.7, [(0.0, ring)]), -19))

# Мобильник: дробь из трёх уведомлений — вибрация по столу + нейтральный «блип».
x = load("1034", "highpass=f=120")
buzz_at = onsets(x, -14, 0.3)[2]
buzz = norm(fade(cut(x, buzz_at + 0.2, buzz_at + 0.56), 0.01, 0.05), peak=0.55)
blip = np.concatenate([tone([(1760, 1.0), (3520, 0.35)], 0.09, 0.05),
                       tone([(2349, 1.0), (4698, 0.3)], 0.20, 0.07)]) * 0.5
events = []
for t in (0.0, 0.5, 1.0):
    events += [(t, blip), (t + 0.02, buzz)]
loop("mobile", norm(place(2.5, events), -21))

# Принтер: струйная печать — стрёкот каретки и жужжание протяжки.
x = load("0169", "highpass=f=150")
loop("printer", norm(seamless(cut(x, 4.6, 14.4), 9.0, 0.6), -21))

# Клавиатура: быстрый набор на настоящей клавиатуре.
x = load("1734", "highpass=f=200")
loop("keyboard", norm(seamless(cut(x, 10.0, 22.6), 12.0, 0.4), -23))

# Системник: вентиляторы компьютера, середина приподнята для динамика телефона.
x = load("0125", "highpass=f=60,equalizer=f=1100:t=q:w=0.9:g=7,equalizer=f=2600:t=q:w=1.2:g=4")
loop("pc", norm(seamless(cut(x, 0.3, 9.9), 8.4, 1.1), -21))

# ---------- фоновые источники ----------

# Лампа: гул трансформатора + дребезг гармоник 100 Гц с неровным мерцанием.
L = 8.0
hum = seamless(cut(load("1091", "highpass=f=350,lowpass=f=4200"), 2.0, 11.2), L, 1.0)
t = np.arange(n(L)) / SR
buzz100 = sum(np.sin(2 * np.pi * 100 * k * t + rng.uniform(0, 6.28)) / k ** 0.7
              for k in range(4, 46))
flutter = 1 + sum(0.07 * np.sin(2 * np.pi * (c / L) * t + rng.uniform(0, 6.28))
                  for c in (3, 7, 13, 29, 53))
lamp = norm(hum, -21) + norm(buzz100 * flutter, -24)
loop("lamp", norm(lamp, -21))

# Кондиционер: ровный поток воздуха.
x = load("1471", "highpass=f=90,lowpass=f=4200,equalizer=f=900:t=q:w=1:g=3")
loop("ac", norm(seamless(cut(x, 10.0, 23.8), 12.0, 1.6), -21))

# Часы: настоящее «тик-так», два полных периода.
x = load("0007", "highpass=f=300")
ticks = onsets(x, -20, 0.3)
period = float(np.median(np.diff(ticks)))
core = cut(x, ticks[2] - 0.03, ticks[2] - 0.03 + 4 * period)
loop("clock", norm(fade(core, 0.005, 0.05), -21))

# Улица: городской перекрёсток.
x = load("2722", "highpass=f=90")
loop("street", norm(seamless(cut(x, 202.0, 222.5), 18.0, 2.2), -21))

# ---------- предметы ----------

# Кот: лёгкий пластиковый стук (механизм пластикового метронома), раз в 0.7 с.
x = load("0468", "highpass=f=400")
taps = onsets(x, -14, 0.2)
tap_a = norm(fade(cut(x, taps[3], taps[3] + 0.11), 0.001, 0.05), peak=0.5)
tap_b = norm(fade(cut(x, taps[6], taps[6] + 0.11), 0.001, 0.05), peak=0.42)
loop("cat", place(1.4, [(0.0, tap_a), (0.7, tap_b)]))

# Поломка лапы: сухой хруст.
x = load("1301")
shot("break", norm(fade(cut(x, 2.06, 2.42), 0.002, 0.08), peak=0.5))

# Кофе: глотки и всасывание воздуха из пустой кружки.
x = load("0508")
shot("sip-1", norm(fade(band(cut(x, 0.78, 1.24), 150, 1900), 0.02, 0.1), peak=0.5))
shot("sip-2", norm(fade(band(cut(x, 3.08, 3.50), 150, 1700), 0.02, 0.1), peak=0.5))
shot("empty-cup", norm(fade(cut(x, 0.12, 1.22), 0.01, 0.12), peak=0.5))

# Пупырка: шесть разных настоящих хлопков плёнки.
x = load("0462")
for i, at in enumerate(onsets(x, -16, 0.4)[:6]):
    shot(f"pop-{i + 1}", norm(fade(cut(x, at, at + 0.14), 0.001, 0.06), peak=0.5))

# ---------- онбординг ----------

x = load("0036")
click_at = onsets(x, -10, 0.05)[0]
shot("switch", norm(fade(cut(x, click_at, click_at + 0.16), 0.001, 0.06), peak=0.4))

x = load("0165", "highpass=f=60")
steps = onsets(x, -14, 0.3)
shot("step-1", norm(fade(cut(x, steps[1], steps[1] + 0.28), 0.003, 0.1), peak=0.5))
shot("step-2", norm(fade(cut(x, steps[2], steps[2] + 0.28), 0.003, 0.1), peak=0.5))

x = cut(load("0666", "highpass=f=120"), 50.0, 53.0)
e, win = env(x, 0.01)
k = int(np.argmax(np.convolve(e, np.ones(35), "valid")))
shot("chair", norm(fade(x[n(k * win):n(k * win + 0.36)], 0.02, 0.12), peak=0.5))

# ---------- общие ----------

# Room tone: тихая атмосфера помещения, без узнаваемых событий.
x = load("2458", "highpass=f=70,lowpass=f=1600")
loop("room", norm(seamless(cut(x, 50.0, 84.5), 32.0, 2.2), -26), kbps=96)

# Пульс: настоящее сердцебиение, два удара на петлю; добавлены гармоники,
# чтобы удар был слышен и на динамике телефона.
x = load("0218")
beats = onsets(band(x, None, 300), -12, 0.45)
def beat(at):
    b = cut(x, at, at + 0.55)
    b = b + 0.55 * band(np.tanh(7 * b), 140, 700)
    return fade(b, 0.004, 0.12)
loop("pulse", norm(place(1.5, [(0.0, beat(beats[2])), (0.75, beat(beats[3]))]), -16))

# Верное действие: короткий чистый двухнотный сигнал.
ok = np.concatenate([tone([(784, 1.0), (1568, 0.25)], 0.08, 0.06),
                     tone([(1175, 1.0), (2350, 0.2)], 0.18, 0.07)])
shot("success", norm(ok, peak=0.2))

# Касание предмета: глухой стук по дереву. Промах: пустой шорох воздуха.
shot("touch", norm(fade(band(cut(load("1588"), 0.0, 0.1), 80, 700), 0.001, 0.05), peak=0.5))
shot("miss", norm(fade(band(cut(load("0128"), 0.06, 0.2), 900, 3200), 0.03, 0.08), peak=0.14))

# Кнопка интерфейса: щелчок мыши. Результат: звонок микроволновки «день готов».
x = load("1735")
at = onsets(x, -12, 0.05)[0]
shot("button", norm(fade(cut(x, at, at + 0.07), 0.001, 0.03), peak=0.3))
shot("result", norm(fade(cut(load("1631", "highpass=f=300"), 0.0, 1.3), 0.002, 0.5), peak=0.45))

with open(os.path.join(OUT, "loops.json"), "w") as f:
    json.dump({"loopAt": LOOP_AT, "length": loops}, f, indent=1)
print("ok:", len(os.listdir(OUT)), "files in", OUT)
