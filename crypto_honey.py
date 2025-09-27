"""Honey encryption (toy distribution-transforming encoder)."""

from __future__ import annotations

import hashlib
import math
import secrets
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

DEFAULT_R = 10 ** 6


class HoneyFormatError(Exception):
    """Raised when a Honey Encryption blob is malformed."""


@dataclass(frozen=True)
class _Universe:
    name: str
    messages: Tuple[str, ...]
    probs: Tuple[float, ...]
    intervals: Tuple[Tuple[int, int], ...]
    R: int


_UNIVERSES: Dict[str, _Universe] = {}


def _ensure_ascii(name: str) -> bytes:
    try:
        encoded = name.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("Universe name must be ASCII") from exc
    if not encoded:
        raise ValueError("Universe name must be non-empty")
    if len(encoded) > 255:
        raise ValueError("Universe name must be <= 255 bytes")
    return encoded


def _normalise_messages(messages: Iterable[str]) -> Tuple[str, ...]:
    result = tuple(str(m) for m in messages)
    if not result:
        raise ValueError("Universe must contain at least one message")
    if any(not isinstance(m, str) or not m for m in result):
        raise ValueError("All universe messages must be non-empty strings")
    return result


def _normalise_probs(probs: Iterable[float], count: int) -> Tuple[float, ...]:
    values = tuple(float(p) for p in probs)
    if len(values) != count:
        raise ValueError("messages and probs must have the same length")
    if any(p <= 0.0 for p in values):
        raise ValueError("All probabilities must be positive")
    total = math.fsum(values)
    if not math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-8):
        raise ValueError("Probabilities must sum to 1.0")
    return values


def _build_intervals(probs: Sequence[float], R: int) -> Tuple[Tuple[int, int], ...]:
    if R <= 0:
        raise ValueError("R must be positive")
    intervals: List[Tuple[int, int]] = []
    total = 0
    remaining_slots = R
    remaining_items = len(probs)
    for prob in probs:
        remaining_items -= 1
        slots = int(round(prob * R))
        if slots <= 0:
            slots = 1
        if slots > remaining_slots - remaining_items:
            slots = max(1, remaining_slots - remaining_items)
        start = total
        end = start + slots
        intervals.append((start, end))
        total = end
        remaining_slots -= slots
    if intervals[-1][1] != R:
        start, _ = intervals[-1]
        intervals[-1] = (start, R)
    if intervals[-1][0] >= intervals[-1][1]:
        raise ValueError("Invalid probability distribution; intervals collapsed")
    return tuple(intervals)


def register_universe(
    name: str,
    messages: List[str],
    probs: List[float],
    *,
    R: int = DEFAULT_R,
) -> None:
    """Register or replace a Honey Encryption message universe.

    Args:
        name: ASCII identifier stored inside the blob.
        messages: Ordered list of plausible plaintexts.
        probs: Matching probability masses (must sum to 1.0).
        R: Resolution of the integer lattice (defaults to 10**6).

    Raises:
        ValueError: If validation fails.

    Example:
        >>> register_universe('demo', ['A', 'B'], [0.6, 0.4])
    """

    _ensure_ascii(name)
    msg_tuple = _normalise_messages(messages)
    prob_tuple = _normalise_probs(probs, len(msg_tuple))
    intervals = _build_intervals(prob_tuple, R)
    _UNIVERSES[name] = _Universe(
        name=name,
        messages=msg_tuple,
        probs=prob_tuple,
        intervals=intervals,
        R=R,
    )


def list_universes() -> List[str]:
    """Return the sorted list of registered universe names."""

    return sorted(_UNIVERSES.keys())


def _get_universe(universe_name: str) -> _Universe:
    universe = _UNIVERSES.get(universe_name)
    if universe is None:
        raise HoneyFormatError(f"Unknown universe '{universe_name}'")
    return universe


def _interval_for_message(universe: _Universe, message: str) -> Tuple[int, int]:
    try:
        idx = universe.messages.index(message)
    except ValueError as exc:
        raise HoneyFormatError(
            f"Message '{message}' is not part of universe '{universe.name}'"
        ) from exc
    return universe.intervals[idx]


def _message_for_seed(universe: _Universe, seed: int) -> str:
    if not (0 <= seed < universe.R):
        raise HoneyFormatError("Seed outside lattice range")
    for (start, end), message in zip(universe.intervals, universe.messages):
        if start <= seed < end:
            return message
    last_start, last_end = universe.intervals[-1]
    if seed == universe.R and last_start < last_end:
        return universe.messages[-1]
    raise HoneyFormatError("Seed does not map to any message interval")


def _parse_blob(blob: bytes) -> Tuple[int, bytes, str, int]:
    if not isinstance(blob, (bytes, bytearray, memoryview)):
        raise HoneyFormatError("Honey payload must be bytes-like")
    data = memoryview(bytes(blob))
    minimum = 6 + 4 + 8 + 1 + 4
    if len(data) < minimum:
        raise HoneyFormatError("Honey payload is too short")
    if bytes(data[:6]) != b"HONEY1":
        raise HoneyFormatError("Missing HONEY1 magic header")
    offset = 6
    R = int.from_bytes(data[offset:offset + 4], "big")
    offset += 4
    nonce = bytes(data[offset:offset + 8])
    offset += 8
    univ_len = data[offset]
    offset += 1
    if len(data) < offset + univ_len + 4:
        raise HoneyFormatError("Honey payload truncated while reading universe")
    universe_name = bytes(data[offset:offset + univ_len]).decode("ascii", errors="strict")
    offset += univ_len
    c = int.from_bytes(data[offset:offset + 4], "big")
    offset += 4
    if offset != len(data):
        extra = len(data) - offset
        if extra:
            raise HoneyFormatError(f"Unexpected {extra} trailing byte(s) in Honey payload")
    return R, nonce, universe_name, c


def _derive_pad(key_int: int, nonce: bytes, R: int) -> int:
    digest = hashlib.sha256(str(int(key_int)).encode("utf-8") + nonce).digest()
    return int.from_bytes(digest, "big") % R


def he_encrypt(message: str, key_int: int, universe_name: str = "default") -> bytes:
    """Encode *message* with Honey Encryption using *key_int*.

    Args:
        message: Plaintext string belonging to the selected universe.
        key_int: Numeric key (deterministic PRF input).
        universe_name: Registered universe identifier.

    Returns:
        Bytes making up the Honey Encryption blob.

    Example:
        >>> blob = he_encrypt('Meeting at 3pm', 1234, 'office_msgs')
        >>> blob.startswith(b'HONEY1')
        True
    """

    universe = _get_universe(universe_name)
    lattice_start, lattice_end = _interval_for_message(universe, str(message))
    width = lattice_end - lattice_start
    if width <= 0:
        raise HoneyFormatError("Universe interval width is zero; adjust probabilities")
    seed_offset = secrets.randbelow(width)
    seed = lattice_start + seed_offset
    nonce = secrets.token_bytes(8)
    pad = _derive_pad(int(key_int), nonce, universe.R)
    c = (seed + pad) % universe.R
    univ_bytes = universe.name.encode("ascii")
    parts = [
        b"HONEY1",
        universe.R.to_bytes(4, "big"),
        nonce,
        len(univ_bytes).to_bytes(1, "big"),
        univ_bytes,
        c.to_bytes(4, "big"),
    ]
    return b"".join(parts)


def he_decrypt(blob: bytes, key_int: int) -> str:
    """Decode a Honey Encryption *blob* with *key_int*.

    Args:
        blob: Bytes previously returned by :func:`he_encrypt`.
        key_int: Numeric key used during encoding.

    Returns:
        The plaintext string selected by the derived seed.

    Raises:
        HoneyFormatError: If the blob cannot be parsed.

    Example:
        >>> blob = he_encrypt('Meeting at 3pm', 1234, 'office_msgs')
        >>> he_decrypt(blob, 1234)
        'Meeting at 3pm'
    """

    R, nonce, universe_name, c = _parse_blob(blob)
    universe = _get_universe(universe_name)
    if R != universe.R:
        raise HoneyFormatError(
            f"Resolution mismatch for universe '{universe_name}' (blob {R}, registry {universe.R})"
        )
    pad = _derive_pad(int(key_int), nonce, universe.R)
    seed = (c - pad) % universe.R
    return _message_for_seed(universe, seed)


def _uniform_probs(messages: Sequence[str]) -> List[float]:
    count = len(messages)
    if count <= 0:
        raise ValueError("Universe must contain at least one message")
    prob = 1.0 / count
    return [prob] * count


_OFFICE_MSGS = [
    "Meeting at 3pm",
    "Budget draft v2",
    "Invoice approved",
    "On leave tomorrow",
    "Lunch order ready",
    "Quarterly report posted",
]

_PASSWORDISH = [
    "Welcome2025!",
    "SITuser#123",
    "P@sswordReset42",
    "MyLaptop_2024",
    "AlphaOmega77",
    "ChangeMeNow!",
]

_SHORT_NOTES = [
    "Call the client",
    "Pick up laundry",
    "Printer jam cleared",
    "Remember the tokens",
    "Check server status",
    "Update documentation",
]

register_universe("office_msgs", list(_OFFICE_MSGS), _uniform_probs(_OFFICE_MSGS))
register_universe("passwordish", list(_PASSWORDISH), _uniform_probs(_PASSWORDISH))
register_universe("short_notes", list(_SHORT_NOTES), _uniform_probs(_SHORT_NOTES))
register_universe("default", list(_SHORT_NOTES), _uniform_probs(_SHORT_NOTES))
