#!/usr/bin/env python3
"""参考音频听感分析：调性 / 听感来源 / 编制 / 节奏动机。

只用于分析参考曲，输出风格参数，不复制旋律、不采样、不变调。
依赖：afconvert（Mac 自带，解码非 WAV）、numpy/scipy/librosa/soundfile。
用法：video analyze <音频路径> [--format text|json]
"""
import argparse
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import find_peaks, resample_poly, welch

try:
    import librosa
except ImportError:
    librosa = None

TARGET_SR = 22050
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def decode_to_wav(src: Path, workdir: Path) -> Path:
    if src.suffix.lower() in (".wav", ".wave"):
        return src
    if shutil.which("afconvert") is None:
        raise RuntimeError("缺少 afconvert，无法解码非 WAV 音频")
    out = workdir / "decoded.wav"
    subprocess.run(
        ["afconvert", "-f", "WAVE", "-d", f"LEI16@{TARGET_SR}", "-c", "1", str(src), str(out)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out


def load_mono(path: Path):
    data, sr = sf.read(str(path), always_2d=False)
    if data.ndim > 1:
        data = data.mean(axis=1)
    data = np.asarray(data, dtype=np.float64)
    if sr != TARGET_SR:
        g = math.gcd(int(sr), TARGET_SR)
        data = resample_poly(data, TARGET_SR // g, int(sr) // g)
        sr = TARGET_SR
    return data, sr


def estimate_bpm(onset_env: np.ndarray, sr: int, hop: int = 512):
    """用 onset 自相关估 BPM，比 librosa tempo 更少落到半速。"""
    if len(onset_env) < hop:
        return 0.0
    env = onset_env - onset_env.mean()
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    min_lag = max(1, int(60 * sr / hop / 200))
    max_lag = min(len(ac) - 1, int(60 * sr / hop / 60))
    if max_lag <= min_lag:
        return 0.0
    lag = int(np.argmax(ac[min_lag : max_lag + 1]) + min_lag)
    return 60 * sr / hop / lag


def estimate_key(chroma: np.ndarray):
    v = chroma / max(chroma.sum(), 1e-9)
    best = None
    for mode, profile in (("major", MAJOR), ("minor", MINOR)):
        p = profile / profile.sum()
        for k in range(12):
            score = float(np.corrcoef(v, np.roll(p, k))[0, 1])
            if best is None or score > best[1]:
                best = (f"{NOTE_NAMES[k]} {mode}", score)
    return best[0], round(best[1], 3)


def formant_peaks(y: np.ndarray, sr: int):
    f, p = welch(y, fs=sr, nperseg=8192)
    mask = (f >= 250) & (f <= 2600)
    band_p = p[mask]
    band_f = f[mask]
    if len(band_p) < 10:
        return []
    dist = max(3, int(sr * 0.07 / max((band_f[1] - band_f[0]), 1e-9)))
    idx, _ = find_peaks(band_p, distance=dist, prominence=band_p.max() * 0.02)
    idx = idx[np.argsort(band_p[idx])[::-1]][:10]
    return [round(float(band_f[i])) for i in sorted(idx)]


def analyze(path: Path):
    with tempfile.TemporaryDirectory(prefix=".audio-analysis-", dir=str(Path.cwd())) as td:
        wav = decode_to_wav(path, Path(td))
        y, sr = load_mono(wav)

    duration = round(len(y) / sr, 2)
    if librosa is None:
        raise RuntimeError("缺少 librosa，请先运行 video doctor / 安装 requirements.txt")

    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=512)
    tempo = estimate_bpm(onset_env, sr)

    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr, units="frames")
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    intervals = np.diff(onset_times)
    intervals = intervals[(intervals > 0.05) & (intervals < 2.0)]

    chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr).mean(axis=1)
    chroma_cqt = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    chroma_cens = librosa.feature.chroma_cens(y=y, sr=sr).mean(axis=1)
    key_stft = estimate_key(chroma_stft)
    key_cqt = estimate_key(chroma_cqt)
    key_cens = estimate_key(chroma_cens)

    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    flatness = float(librosa.feature.spectral_flatness(y=y).mean())
    entropy = float(-(chroma_stft * np.log2(chroma_stft + 1e-9)).sum() / math.log2(12))
    formants = formant_peaks(y, sr)

    if flatness < 0.08 and len(formants) >= 2:
        source = "强谐波 + 多共振峰：很可能含真人/合成童声合唱，纯器乐难做到神似"
        arrangement = "优先人声或共振峰合成；器乐只做支撑"
    elif flatness < 0.15:
        source = "谐波为主：旋律/和声可辨识，可能是清晰器乐或轻人声"
        arrangement = "可用号角/弦乐/拨弦，若目标像合唱仍需人声层"
    else:
        source = "宽频/高噪声：失真吉他、鼓组或密集打击占主导"
        arrangement = "摇滚/电子编制更接近，旋律需依附节奏动机"

    result = {
        "file": str(path),
        "duration_sec": duration,
        "sample_rate": sr,
        "bpm": round(tempo, 1),
        "onset_interval_median_sec": round(float(np.median(intervals)), 3) if len(intervals) else None,
        "key_stft": {"key": key_stft[0], "corr": key_stft[1]},
        "key_cqt": {"key": key_cqt[0], "corr": key_cqt[1]},
        "key_cens": {"key": key_cens[0], "corr": key_cens[1]},
        "spectral_centroid_hz": round(centroid),
        "spectral_flatness": round(flatness, 4),
        "chroma_entropy": round(entropy, 3),
        "formant_peaks_hz": formants,
        "source_guess": source,
        "arrangement_hint": arrangement,
        "prompt_priority": "调性 > 听感来源(人声/器乐) > 编制 > 节奏动机 > 旋律",
    }
    return result


def main():
    ap = argparse.ArgumentParser(description="参考音频听感分析（不复制旋律）")
    ap.add_argument("audio", help="MP3/WAV/M4A 等音频路径")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    args = ap.parse_args()

    path = Path(args.audio).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"音频不存在: {path}")

    result = analyze(path)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"文件: {result['file']}")
    print(f"时长: {result['duration_sec']}s | 采样率: {result['sample_rate']}Hz")
    print(f"BPM: {result['bpm']} | onset 中位间隔: {result['onset_interval_median_sec']}s")
    print(
        "调性: "
        f"STFT={result['key_stft']['key']}({result['key_stft']['corr']}) "
        f"CQT={result['key_cqt']['key']}({result['key_cqt']['corr']}) "
        f"CENS={result['key_cens']['key']}({result['key_cens']['corr']})"
    )
    print(f"频谱质心: {result['spectral_centroid_hz']}Hz | 平坦度: {result['spectral_flatness']} | chroma 熵: {result['chroma_entropy']}")
    print(f"共振峰: {result['formant_peaks_hz']}")
    print(f"听感来源: {result['source_guess']}")
    print(f"编制建议: {result['arrangement_hint']}")
    print(f"Prompt 优先级: {result['prompt_priority']}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"分析失败: {exc}", file=sys.stderr)
        raise SystemExit(1)
