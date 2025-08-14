"""Optional CPU-only trainable demos over deterministic synthetic data."""

from __future__ import annotations

from dataclasses import dataclass


def torch_available() -> bool:
    try:
        import torch  # noqa: F401
    except ImportError:
        return False
    return True


@dataclass(frozen=True, slots=True)
class TrainingSummary:
    initial_loss: float
    final_loss: float
    steps: int
    data_origin: str = "deterministic-synthetic"


def train_vq_demo(seed: int = 0, steps: int = 40) -> TrainingSummary:
    """Fit a tiny VQ-like bottleneck to synthetic formant-feature clusters."""
    if steps <= 0:
        raise ValueError("training steps must be positive")
    try:
        import torch
    except ImportError as error:
        raise RuntimeError("install the torch extra for model demos") from error
    torch.manual_seed(seed)
    inputs = torch.cat((torch.randn(32, 4) * 0.05 - 1, torch.randn(32, 4) * 0.05 + 1))
    encoder = torch.nn.Linear(4, 2)
    decoder = torch.nn.Linear(2, 4)
    optimizer = torch.optim.Adam([*encoder.parameters(), *decoder.parameters()], lr=0.03)
    losses: list[float] = []
    for _ in range(steps):
        latent = encoder(inputs)
        quantized = torch.round(latent * 4) / 4
        quantized = latent + (quantized - latent).detach()
        loss = torch.mean((decoder(quantized) - inputs) ** 2)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    return TrainingSummary(round(losses[0], 6), round(losses[-1], 6), steps)


def train_lm_demo(seed: int = 0, steps: int = 30) -> TrainingSummary:
    """Train a small causal next-token table on a planted repeating stream."""
    if steps <= 0:
        raise ValueError("training steps must be positive")
    try:
        import torch
    except ImportError as error:
        raise RuntimeError("install the torch extra for model demos") from error
    torch.manual_seed(seed)
    sequence = torch.tensor([0, 1, 2, 3] * 16)
    logits = torch.nn.Parameter(torch.zeros(4, 4))
    optimizer = torch.optim.Adam([logits], lr=0.15)
    losses: list[float] = []
    for _ in range(steps):
        loss = torch.nn.functional.cross_entropy(logits[sequence[:-1]], sequence[1:])
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach()))
    return TrainingSummary(round(losses[0], 6), round(losses[-1], 6), steps)


def constrained_sample(
    logits: list[float], allowed: tuple[int, ...], *, temperature: float = 1.0
) -> int:
    """Choose the greatest allowed scaled logit with deterministic tie breaking."""
    if temperature <= 0 or not allowed or any(not 0 <= index < len(logits) for index in allowed):
        raise ValueError("sampling constraints are invalid")
    return max(allowed, key=lambda index: (logits[index] / temperature, -index))
