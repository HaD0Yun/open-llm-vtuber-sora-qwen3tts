#!/usr/bin/env python3
import argparse
import json
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import a March7 Live2D folder into live2d-models/march7/runtime"
    )
    parser.add_argument("source", help="Path to extracted March7 model directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source}")

    repo_root = Path(__file__).resolve().parents[1]
    target_runtime = repo_root / "live2d-models" / "march7" / "runtime"
    target_runtime.parent.mkdir(parents=True, exist_ok=True)

    if target_runtime.exists():
        shutil.rmtree(target_runtime)
    shutil.copytree(source, target_runtime)

    model3_candidates = list(target_runtime.glob("*.model3.json"))
    if not model3_candidates:
        raise FileNotFoundError("No .model3.json found in imported source")

    original_model3 = model3_candidates[0]
    model_data = json.loads(original_model3.read_text(encoding="utf-8"))

    for group in model_data.get("Groups", []):
        if group.get("Name") == "LipSync":
            group["Ids"] = ["ParamMouthOpenY"]

    target_model3 = target_runtime / "march7.model3.json"
    target_model3.write_text(
        json.dumps(model_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Imported March7 model to: {target_runtime}")
    print(f"Patched model file: {target_model3}")


if __name__ == "__main__":
    main()
