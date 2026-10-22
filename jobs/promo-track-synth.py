"""Upbeat electronic track for the 42 s animatic: 124 BPM, kick, clap, hats, bass, chords, risers and three drops at 2.42 s, 18.10 s and 37.60 s. Pure Python, writes a 16-bit stereo WAV."""
import math, random, struct, sys, array
SR = 44100; DUR = 42.0; BPM = 124.0; BEAT = 60.0 / BPM; N = int(SR * DUR)
random.seed(7)
drums = [0.0] * N; tonal = [0.0] * N; fx = [0.0] * N
def add(buf, start, samples, gain=1.0):
    i0 = int(start * SR)
    for k, v in enumerate(samples):
        j = i0 + k
        if 0 <= j < N: buf[j] += v * gain
def env_exp(n, tau): return [math.exp(-k / (tau * SR)) for k in range(n)]
def kick(t, punch=1.0):
    n = int(0.42 * SR); out = []; ph = 0.0
    for k in range(n):
        f = 42 + 140 * math.exp(-k / (0.045 * SR)); ph += 2 * math.pi * f / SR
        out.append(math.tanh(2.2 * math.sin(ph)) * math.exp(-k / (0.16 * SR)) * punch)
    return out
def clap(t):
    n = int(0.22 * SR); out = []
    for k in range(n):
        a = (math.exp(-k / (0.035 * SR)) + 0.6 * math.exp(-max(0, k - 900) / (0.03 * SR)) + 0.4 * math.exp(-max(0, k - 1800) / (0.06 * SR)))
        out.append((random.random() * 2 - 1) * a * 0.9)
    # body
    return [v + 0.25 * math.sin(2 * math.pi * 180 * k / SR) * math.exp(-k / (0.03 * SR)) for k, v in enumerate(out)]
def hat(t, open_=False):
    n = int((0.16 if open_ else 0.045) * SR); prev = 0.0; out = []
    for k in range(n):
        x = random.random() * 2 - 1; y = x - prev; prev = x  # crude highpass
        out.append(y * 0.5 * math.exp(-k / ((0.05 if open_ else 0.012) * SR)))
    return out
def bass(t, freq, length, drive=1.0):
    n = int(length * SR); out = []; ph = 0.0; y = 0.0; a = 1 - math.exp(-2 * math.pi * 520 / SR)
    for k in range(n):
        ph += 2 * math.pi * freq / SR
        saw = (ph / math.pi) % 2 - 1; sq = 1.0 if math.sin(ph) > 0 else -1.0
        x = 0.6 * saw + 0.4 * sq; y += a * (x - y)
        e = min(1.0, k / (0.004 * SR)) * (math.exp(-max(0, k - n + int(0.06 * SR)) / (0.02 * SR)) if k > n - int(0.06 * SR) else 1.0)
        out.append(math.tanh(drive * y) * e * 0.8)
    return out
def sub(t, freq, length):
    n = int(length * SR); return [math.sin(2 * math.pi * freq * k / SR) * min(1.0, k / (0.01 * SR)) * (1.0 if k < n - int(0.05 * SR) else math.exp(-(k - n + int(0.05 * SR)) / (0.02 * SR))) for k in range(n)]
def chord(t, freqs, length, attack=0.4):
    n = int(length * SR); out = [0.0] * n
    for f in freqs:
        for d in (-0.4, 0.4):
            fd = f * (2 ** (d / 1200.0)); ph = 0.0
            for k in range(n):
                ph += 2 * math.pi * fd / SR; e = min(1.0, k / (attack * SR)) * (1.0 if k < n - int(0.3 * SR) else math.exp(-(k - n + int(0.3 * SR)) / (0.12 * SR)))
                out[k] += math.sin(ph) * e / (len(freqs) * 2)
    return out
def riser(t, length):
    n = int(length * SR); out = []; prev = 0.0; ph = 0.0
    for k in range(n):
        p = k / n; x = random.random() * 2 - 1; y = x - 0.6 * prev; prev = x
        f = 120 * (2 ** (p * 4)); ph += 2 * math.pi * f / SR
        out.append((0.35 * y * (0.2 + 0.8 * p) + 0.25 * math.sin(ph) * p) * (p ** 1.5))
    return out
def impact(t):
    n = int(1.2 * SR); out = []
    for k in range(n):
        out.append(0.9 * math.sin(2 * math.pi * (36 + 30 * math.exp(-k / (0.05 * SR))) * k / SR) * math.exp(-k / (0.5 * SR)) + (random.random() * 2 - 1) * 0.5 * math.exp(-k / (0.08 * SR)))
    return out
NOTE = lambda semis: 55.0 * (2 ** (semis / 12.0))  # 55 Hz = A1
# sections: (start, end, kind) kinds: intro, drop, groove, build, break
SECTIONS = [(0.0, 2.42, 'intro'), (2.42, 10.0, 'drop'), (10.0, 14.0, 'groove'), (14.0, 18.1, 'build'), (18.1, 26.0, 'drop2'), (26.0, 32.0, 'break'), (32.0, 37.6, 'build'), (37.6, 40.5, 'drop2'), (40.5, 42.0, 'outro')]
DROPS = [2.42, 18.1, 37.6]
BASSLINE = [0, 0, 7, 0, 0, 10, 7, 5]   # semitones over A, one per eighth
CHORDS = [[0, 3, 7, 10], [-2, 2, 5, 10], [-4, 0, 3, 7], [-2, 2, 5, 10]]  # Am7, G, F, G in semis from A
def kind_at(t):
    for a, b, k in SECTIONS:
        if a <= t < b: return k
    return 'outro'
beat = 0; t = 0.0; bar = 0
while t < DUR:
    k = kind_at(t); b8 = (beat % 8)
    if k in ('drop', 'drop2', 'groove', 'build'):
        add(drums, t, kick(t, 1.0 if k != 'build' else 0.8))
        if beat % 2 == 1 and k != 'build': add(drums, t, clap(t), 0.7)
        for e in (0, 1): add(drums, t + e * BEAT / 2, hat(t, open_=(e == 1 and beat % 2 == 1)), 0.35 if k != 'build' else 0.25)
        if k == 'build' and (t - 14.0 > 2.0 if t < 18 else t - 32.0 > 3.0):
            for e in range(4): add(drums, t + e * BEAT / 4, clap(t), 0.5)
    if k == 'break':
        if beat % 2 == 0: add(drums, t, kick(t, 0.6), 0.7)
        add(drums, t + BEAT / 2, hat(t), 0.2)
    if k in ('drop', 'drop2', 'groove'):
        for e in (0, 1):
            semi = BASSLINE[(beat * 2 + e) % 8] + ([0, -2, -4, -2][(beat // 4) % 4])
            add(tonal, t + e * BEAT / 2, bass(t, NOTE(semi), BEAT / 2 * 0.95, drive=1.6 if k == 'drop2' else 1.2), 0.9)
            if k == 'drop2': add(tonal, t + e * BEAT / 2, sub(t, NOTE(semi - 12), BEAT / 2 * 0.95), 0.7)
    if k == 'build':
        semi = ([0, -2, -4, -2][(beat // 4) % 4]); add(tonal, t, bass(t, NOTE(semi), BEAT * 0.5, 1.0), 0.5)
    if beat % 4 == 0 and k not in ('intro', 'outro'):
        ch = CHORDS[(beat // 4) % 4]; add(tonal, t, chord(t, [NOTE(s + 24) for s in ch], BEAT * 4, attack=0.05 if k in ('drop', 'drop2') else 0.6), 0.55 if k == 'break' else 0.35)
    beat += 1; t = beat * BEAT
for d in DROPS:
    add(fx, max(0.0, d - 2.4), riser(d, 2.4), 0.8); add(fx, d, impact(d), 1.0)
add(fx, 0.0, riser(0.0, 2.4), 0.6)
# sidechain pump on tonal around every kick in drop/groove sections
pump = [1.0] * N
for i in range(int(DUR / BEAT) + 1):
    t0 = i * BEAT; k = kind_at(t0)
    if k in ('drop', 'drop2', 'groove', 'build'):
        j0 = int(t0 * SR)
        for j in range(j0, min(N, j0 + int(0.28 * SR))): pump[j] = min(pump[j], 0.25 + 0.75 * ((j - j0) / (0.28 * SR)) ** 1.5)
mix = []
for j in range(N):
    tt = j / SR; g = 1.0
    if tt > 40.5: g = max(0.0, 1 - (tt - 40.5) / 1.5)
    v = (drums[j] * 0.9 + tonal[j] * pump[j] * 0.8 + fx[j] * 0.7) * g
    mix.append(math.tanh(v * 1.1))
peak = max(1e-6, max(abs(v) for v in mix)); scale = 0.92 / peak
out = array.array('h', (int(max(-32767, min(32767, v * scale * 32767))) for v in mix for _ in (0, 1)))
path = sys.argv[1]
with open(path, 'wb') as f:
    data = out.tobytes()
    f.write(b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE' + b'fmt ' + struct.pack('<IHHIIHH', 16, 1, 2, SR, SR * 4, 4, 16) + b'data' + struct.pack('<I', len(data)) + data)
print('wrote', path, 'seconds', DUR, 'peak', round(peak, 3))
