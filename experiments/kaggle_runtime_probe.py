from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.backend_adapter import discover_backend_specs


def _redact_env(values: dict[str, str | None]) -> dict[str, str | None]:
    redacted: dict[str, str | None] = {}
    for key, value in values.items():
        if value is None:
            redacted[key] = None
        elif any(token in key.upper() for token in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            redacted[key] = "<redacted>"
        elif len(value) > 96:
            redacted[key] = value[:12] + "…" + value[-8:]
        else:
            redacted[key] = value
    return redacted


def _torch_info() -> dict[str, Any]:
    try:
        import torch

        info: dict[str, Any] = {
            "torch_version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "cuda_version": getattr(torch.version, "cuda", None),
        }
        if torch.cuda.is_available():
            info["gpu_name"] = torch.cuda.get_device_name(0)
        else:
            info["gpu_name"] = None
        return info
    except Exception as err:  # noqa: BLE001 - probe only
        return {
            "torch_error": f"{type(err).__name__}: {err}",
            "torch_available": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("experiments/kaggle_runtime_probe.json"))
    args = parser.parse_args()

    env = {
        "KAGGLE_IS_COMPETITION_RERUN": os.getenv("KAGGLE_IS_COMPETITION_RERUN"),
        "AICOMP_MODEL_NAMES": os.getenv("AICOMP_MODEL_NAMES"),
        "GPT_OSS_GGUF_REPO": os.getenv("GPT_OSS_GGUF_REPO"),
        "GPT_OSS_GGUF_FILE": os.getenv("GPT_OSS_GGUF_FILE"),
        "GPT_OSS_MODEL_PATH": os.getenv("GPT_OSS_MODEL_PATH"),
        "GEMMA_GGUF_REPO": os.getenv("GEMMA_GGUF_REPO"),
        "GEMMA_GGUF_FILE": os.getenv("GEMMA_GGUF_FILE"),
        "GEMMA_MODEL_PATH": os.getenv("GEMMA_MODEL_PATH"),
        "GEMMA4_MODEL_PATH": os.getenv("GEMMA4_MODEL_PATH"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "HF_HOME": os.getenv("HF_HOME"),
    }

    payload = {
        "runtime": {
            "platform": platform.platform(),
            "system": platform.system(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "executable": sys.executable,
        },
        "torch": _torch_info(),
        "env": _redact_env(env),
        "backend_availability": [
            {
                "backend": spec.name,
                "available": spec.available,
                "reason": spec.reason,
            }
            for spec in discover_backend_specs()
        ],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

