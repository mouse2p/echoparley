"""Codebook diagnostics and update mechanics for synthetic VQ experiments."""

from __future__ import annotations

import html
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
IntArray = NDArray[np.int64]


@dataclass(frozen=True, slots=True)
class CodebookHealth:
    size: int
    occupied: int
    occupancy_ratio: float
    perplexity: float
    effective_size: float


def codebook_health(assignments: IntArray, size: int) -> CodebookHealth:
    """Measure occupancy and entropy without implying representation quality."""
    values = np.asarray(assignments, dtype=np.int64)
    if size <= 0 or values.ndim != 1 or np.any((values < 0) | (values >= size)):
        raise ValueError("assignments must be a vector inside the codebook")
    counts = np.bincount(values, minlength=size)
    probabilities = counts[counts > 0] / max(1, len(values))
    entropy = -float(np.sum(probabilities * np.log(probabilities))) if len(values) else 0.0
    perplexity = float(np.exp(entropy))
    occupied = int(np.count_nonzero(counts))
    return CodebookHealth(
        size, occupied, round(occupied / size, 6), round(perplexity, 6), round(perplexity / size, 6)
    )


@dataclass(frozen=True, slots=True)
class CollapseAssessment:
    collapsed: bool
    occupancy_below_threshold: bool
    perplexity_below_threshold: bool


def assess_collapse(
    health: CodebookHealth, *, minimum_occupancy: float = 0.25, minimum_perplexity: float = 2.0
) -> CollapseAssessment:
    """Apply explicit experiment thresholds to codebook diagnostics."""
    if not 0 <= minimum_occupancy <= 1 or minimum_perplexity < 1:
        raise ValueError("collapse thresholds are invalid")
    low_occupancy = health.occupancy_ratio < minimum_occupancy
    low_perplexity = health.perplexity < minimum_perplexity
    return CollapseAssessment(low_occupancy or low_perplexity, low_occupancy, low_perplexity)


@dataclass(frozen=True, slots=True)
class EMACodebook:
    centroids: FloatArray
    counts: FloatArray
    sums: FloatArray


def initialize_ema_codebook(centroids: FloatArray) -> EMACodebook:
    """Initialize running statistics from finite two-dimensional centroids."""
    values = np.asarray(centroids, dtype=np.float64)
    if values.ndim != 2 or not len(values) or not np.all(np.isfinite(values)):
        raise ValueError("EMA centroids must be a nonempty finite matrix")
    counts = np.ones(len(values), dtype=np.float64)
    return EMACodebook(values.copy(), counts, values.copy())


def ema_codebook_step(
    state: EMACodebook,
    embeddings: FloatArray,
    assignments: IntArray,
    *,
    decay: float = 0.99,
    epsilon: float = 1e-5,
) -> EMACodebook:
    """Apply one exponential-moving-average codebook update."""
    values = np.asarray(embeddings, dtype=np.float64)
    identifiers = np.asarray(assignments, dtype=np.int64)
    if not 0 <= decay < 1 or epsilon <= 0:
        raise ValueError("EMA decay and epsilon are invalid")
    if (
        values.ndim != 2
        or values.shape[1] != state.centroids.shape[1]
        or identifiers.shape != (len(values),)
    ):
        raise ValueError("EMA embeddings and assignments must align")
    if np.any((identifiers < 0) | (identifiers >= len(state.centroids))):
        raise ValueError("EMA assignment falls outside codebook")
    batch_counts = np.bincount(identifiers, minlength=len(state.centroids)).astype(np.float64)
    batch_sums = np.zeros_like(state.sums)
    np.add.at(batch_sums, identifiers, values)
    counts = decay * state.counts + (1 - decay) * batch_counts
    sums = decay * state.sums + (1 - decay) * batch_sums
    centroids = sums / np.maximum(counts[:, None], epsilon)
    unused = batch_counts == 0
    centroids[unused] = state.centroids[unused]
    sums[unused] = centroids[unused] * counts[unused, None]
    return EMACodebook(centroids, counts, sums)


def dead_code_indices(counts: FloatArray, *, minimum_count: float = 0.5) -> tuple[int, ...]:
    """Return code indices below an explicit usage-count threshold."""
    values = np.asarray(counts, dtype=np.float64)
    if (
        values.ndim != 1
        or minimum_count < 0
        or not np.all(np.isfinite(values))
        or np.any(values < 0)
    ):
        raise ValueError("dead-code counts and threshold are invalid")
    return tuple(int(index) for index in np.flatnonzero(values < minimum_count))


def revive_dead_codes(
    state: EMACodebook, embeddings: FloatArray, *, minimum_count: float = 0.5, seed: int = 0
) -> EMACodebook:
    """Replace dead centroids with distinct seeded synthetic batch embeddings."""
    values = np.asarray(embeddings, dtype=np.float64)
    dead = dead_code_indices(state.counts, minimum_count=minimum_count)
    if values.ndim != 2 or values.shape[1] != state.centroids.shape[1] or len(values) < len(dead):
        raise ValueError("revival embeddings must cover dead codes and match width")
    if seed < 0:
        raise ValueError("revival seed must be non-negative")
    if not dead:
        return state
    rng = np.random.default_rng(seed)
    chosen = rng.choice(len(values), len(dead), replace=False)
    centroids, counts, sums = state.centroids.copy(), state.counts.copy(), state.sums.copy()
    for code, row in zip(dead, chosen, strict=True):
        centroids[code] = values[row]
        counts[code] = max(1.0, minimum_count)
        sums[code] = centroids[code] * counts[code]
    return EMACodebook(centroids, counts, sums)


@dataclass(frozen=True, slots=True)
class VQLossCurve:
    reconstruction: tuple[float, ...]
    quantization: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.reconstruction or len(self.reconstruction) != len(self.quantization):
            raise ValueError("VQ loss curves must have equal nonzero lengths")
        if any(
            value < 0 or not np.isfinite(value)
            for value in (*self.reconstruction, *self.quantization)
        ):
            raise ValueError("VQ losses must be finite and non-negative")

    @property
    def steps(self) -> int:
        return len(self.reconstruction)


def vq_loss_svg(curve: VQLossCurve, *, title: str = "synthetic VQ loss") -> str:
    """Render reconstruction and quantization loss without plotting dependencies."""
    maximum = max((*curve.reconstruction, *curve.quantization, 1e-12))

    def points(values: tuple[float, ...]) -> str:
        coordinates = []
        for index, value in enumerate(values):
            x = 20 + round(index * 560 / max(1, curve.steps - 1))
            y = 20 + round(160 * (1 - value / maximum))
            coordinates.append(f"{x},{y}")
        return " ".join(coordinates)

    return "\n".join(
        [
            '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="220">',
            '<metadata data-origin="deterministic-synthetic"/>',
            f"<title>{html.escape(title)}</title>",
            f'<polyline class="reconstruction" points="{points(curve.reconstruction)}"/>',
            f'<polyline class="quantization" points="{points(curve.quantization)}"/>',
            "</svg>",
            "",
        ]
    )


def train_vq_loss_curve(seed: int = 0, steps: int = 20) -> VQLossCurve:
    """Train a tiny CPU VQ bottleneck on synthetic clusters and return real losses."""
    if steps <= 0:
        raise ValueError("VQ training steps must be positive")
    try:
        import torch
    except ImportError as error:
        raise RuntimeError("install the torch extra for VQ training") from error
    torch.manual_seed(seed)
    inputs = torch.cat((torch.randn(24, 3) * 0.05 - 1, torch.randn(24, 3) * 0.05 + 1))
    encoder = torch.nn.Linear(3, 2)
    decoder = torch.nn.Linear(2, 3)
    optimizer = torch.optim.Adam((*encoder.parameters(), *decoder.parameters()), lr=0.04)
    reconstruction, quantization = [], []
    for _ in range(steps):
        latent = encoder(inputs)
        quantized = torch.round(latent * 4) / 4
        reconstruction_loss = torch.mean(
            (decoder(latent + (quantized - latent).detach()) - inputs) ** 2
        )
        quantization_loss = torch.mean((latent - quantized.detach()) ** 2)
        loss = reconstruction_loss + 0.25 * quantization_loss
        optimizer.zero_grad()
        loss.backward()  # type: ignore[no-untyped-call]
        optimizer.step()
        reconstruction.append(round(float(reconstruction_loss.detach()), 6))
        quantization.append(round(float(quantization_loss.detach()), 6))
    return VQLossCurve(tuple(reconstruction), tuple(quantization))


def vq_curve_summary(curve: VQLossCurve) -> dict[str, float | int | str]:
    """Report measured loss changes with an explicit synthetic-data label."""
    return {
        "data_origin": "deterministic-synthetic",
        "steps": curve.steps,
        "initial_reconstruction": curve.reconstruction[0],
        "final_reconstruction": curve.reconstruction[-1],
        "initial_quantization": curve.quantization[0],
        "final_quantization": curve.quantization[-1],
    }
