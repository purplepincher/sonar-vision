"""Signal processing — sampling, filtering, and frequency analysis."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class Signal:
    """A discrete-time signal with uniform sampling.

    Attributes:
        samples: Amplitude values.
        sample_rate: Samples per second (Hz).
    """

    samples: list[float] = field(default_factory=list)
    sample_rate: float = 44100.0

    # ── constructors ──────────────────────────────────────────────

    @classmethod
    def sine(cls, frequency: float, duration: float, sample_rate: float = 44100.0, amplitude: float = 1.0) -> Signal:
        """Generate a sine-wave signal."""
        n = int(sample_rate * duration)
        samples = [amplitude * math.sin(2.0 * math.pi * frequency * i / sample_rate) for i in range(n)]
        return cls(samples=samples, sample_rate=sample_rate)

    @classmethod
    def noise(cls, duration: float, sample_rate: float = 44100.0, amplitude: float = 1.0, seed: int | None = None) -> Signal:
        """Generate uniform random noise."""
        import random
        rng = random.Random(seed)
        n = int(sample_rate * duration)
        samples = [amplitude * (rng.random() * 2.0 - 1.0) for _ in range(n)]
        return cls(samples=samples, sample_rate=sample_rate)

    @classmethod
    def chirp(cls, f0: float, f1: float, duration: float, sample_rate: float = 44100.0, amplitude: float = 1.0) -> Signal:
        """Generate a linear chirp from *f0* to *f1* Hz."""
        n = int(sample_rate * duration)
        rate = (f1 - f0) / duration
        samples = [
            amplitude * math.sin(2.0 * math.pi * (f0 * t + 0.5 * rate * t * t))
            for t in (i / sample_rate for i in range(n))
        ]
        return cls(samples=samples, sample_rate=sample_rate)

    # ── properties ────────────────────────────────────────────────

    @property
    def duration(self) -> float:
        """Signal duration in seconds."""
        return len(self.samples) / self.sample_rate if self.sample_rate else 0.0

    @property
    def n_samples(self) -> int:
        return len(self.samples)

    # ── sampling / resampling ─────────────────────────────────────

    def resample(self, target_rate: float) -> Signal:
        """Linear-interpolation resample to *target_rate*."""
        if target_rate <= 0 or not self.samples:
            return Signal(samples=[], sample_rate=target_rate)
        ratio = self.sample_rate / target_rate
        new_n = max(1, int(len(self.samples) / ratio))
        new_samples: list[float] = []
        for i in range(new_n):
            pos = i * ratio
            idx = int(pos)
            frac = pos - idx
            if idx + 1 < len(self.samples):
                new_samples.append(self.samples[idx] * (1.0 - frac) + self.samples[idx + 1] * frac)
            else:
                new_samples.append(self.samples[min(idx, len(self.samples) - 1)])
        return Signal(samples=new_samples, sample_rate=target_rate)

    # ── filtering ─────────────────────────────────────────────────

    def lowpass(self, cutoff: float, order: int = 5) -> Signal:
        """Simple moving-average low-pass filter (approximation).

        Window size is derived from *cutoff* relative to Nyquist.
        """
        nyquist = self.sample_rate / 2.0
        if cutoff <= 0 or cutoff >= nyquist:
            return Signal(samples=list(self.samples), sample_rate=self.sample_rate)
        window = max(1, int(nyquist / cutoff) * order)
        window = min(window, len(self.samples))
        if window <= 1:
            return Signal(samples=list(self.samples), sample_rate=self.sample_rate)
        out: list[float] = []
        half = window // 2
        for i in range(len(self.samples)):
            start = max(0, i - half)
            end = min(len(self.samples), i + half + 1)
            out.append(sum(self.samples[start:end]) / (end - start))
        return Signal(samples=out, sample_rate=self.sample_rate)

    def highpass(self, cutoff: float, order: int = 5) -> Signal:
        """Cascaded high-pass by subtracting low-pass from original."""
        lp = self.lowpass(cutoff, order)
        return Signal(
            samples=[s - l for s, l in zip(self.samples, lp.samples)],
            sample_rate=self.sample_rate,
        )

    def bandpass(self, low_cutoff: float, high_cutoff: float, order: int = 5) -> Signal:
        """Band-pass via lowpass then highpass."""
        return self.lowpass(high_cutoff, order).highpass(low_cutoff, order)

    def threshold(self, level: float) -> Signal:
        """Hard threshold — samples below *level* in absolute value become 0."""
        return Signal(
            samples=[s if abs(s) >= level else 0.0 for s in self.samples],
            sample_rate=self.sample_rate,
        )

    def envelope(self) -> Signal:
        """Simple magnitude envelope via sliding maximum of absolute value."""
        if not self.samples:
            return Signal(sample_rate=self.sample_rate)
        window = max(1, int(self.sample_rate * 0.005))  # 5 ms window
        out: list[float] = []
        for i in range(len(self.samples)):
            start = max(0, i - window)
            out.append(max(abs(s) for s in self.samples[start : i + 1]))
        return Signal(samples=out, sample_rate=self.sample_rate)

    # ── analysis ──────────────────────────────────────────────────

    def rms(self) -> float:
        """Root-mean-square amplitude."""
        if not self.samples:
            return 0.0
        return math.sqrt(sum(s * s for s in self.samples) / len(self.samples))

    def peak(self) -> float:
        """Peak (max absolute) amplitude."""
        if not self.samples:
            return 0.0
        return max(abs(s) for s in self.samples)

    def snr_db(self, noise: Signal) -> float:
        """Signal-to-noise ratio in dB relative to *noise*."""
        sig_power = self.rms()
        noise_power = noise.rms()
        if noise_power == 0.0:
            return float("inf") if sig_power > 0 else 0.0
        return 20.0 * math.log10(sig_power / noise_power)

    def energy(self) -> float:
        """Total signal energy."""
        return sum(s * s for s in self.samples)

    def dominant_frequency(self) -> float:
        """Estimate dominant frequency via zero-crossing count."""
        if len(self.samples) < 2:
            return 0.0
        crossings = 0
        for i in range(1, len(self.samples)):
            if self.samples[i - 1] * self.samples[i] < 0:
                crossings += 1
        return (crossings / 2.0) * self.sample_rate / len(self.samples)

    def dft_magnitude(self, n: int | None = None) -> list[float]:
        """Compute DFT magnitude spectrum (naïve O(N²), for small signals).

        Returns list of magnitudes for bins 0 … N/2.
        """
        N = n or len(self.samples)
        N = min(N, len(self.samples))
        magnitudes: list[float] = []
        half = N // 2 + 1
        for k in range(half):
            re = 0.0
            im = 0.0
            for n_idx in range(N):
                angle = 2.0 * math.pi * k * n_idx / N
                re += self.samples[n_idx] * math.cos(angle)
                im -= self.samples[n_idx] * math.sin(angle)
            magnitudes.append(math.sqrt(re * re + im * im) / N)
        return magnitudes

    # ── arithmetic ────────────────────────────────────────────────

    def __add__(self, other: Signal) -> Signal:
        if self.sample_rate != other.sample_rate:
            raise ValueError("Sample rates must match for addition")
        n = max(len(self.samples), len(other.samples))
        a = self.samples + [0.0] * (n - len(self.samples))
        b = other.samples + [0.0] * (n - len(other.samples))
        return Signal(samples=[x + y for x, y in zip(a, b)], sample_rate=self.sample_rate)

    def __mul__(self, other: float | Signal) -> Signal:
        if isinstance(other, Signal):
            if self.sample_rate != other.sample_rate:
                raise ValueError("Sample rates must match")
            return Signal(
                samples=[a * b for a, b in zip(self.samples, other.samples)],
                sample_rate=self.sample_rate,
            )
        return Signal(samples=[s * other for s in self.samples], sample_rate=self.sample_rate)
