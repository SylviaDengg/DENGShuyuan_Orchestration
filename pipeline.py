import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List

from crews import get_evaluation_crew, get_intake_crew, get_reporting_crew


CHECKPOINT_PATH = Path("checkpoint.json")
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 1
CHECKPOINT_INPUT_KEY = "input_claim"
STAGE_NAMES = ("intake", "evaluation", "reporting")


def log(message: str) -> None:
    print(message, flush=True)


def load_checkpoint(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise RuntimeError("checkpoint.json must contain a JSON object.")

    return {str(key): str(value) for key, value in data.items()}


def save_checkpoint(path: Path, checkpoint: Dict[str, str]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(checkpoint, file, indent=2, ensure_ascii=False)


def extract_result_text(result: Any) -> str:
    raw_output = getattr(result, "raw", None)
    if isinstance(raw_output, str) and raw_output.strip():
        return raw_output.strip()

    return str(result).strip()


class OrchestrationPipeline:
    def __init__(
        self,
        checkpoint_path: Path = CHECKPOINT_PATH,
        max_retries: int = MAX_RETRIES,
        base_delay_seconds: int = BASE_DELAY_SECONDS,
    ) -> None:
        self.checkpoint_path = checkpoint_path
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds

    def run_stage(
        self,
        stage_name: str,
        crew_factory: Callable[[], Any],
        inputs: Dict[str, str],
    ) -> str:
        for attempt in range(1, self.max_retries + 1):
            try:
                crew = crew_factory()
                result = crew.kickoff(inputs=inputs)
                result_text = extract_result_text(result)
                if not result_text:
                    raise RuntimeError("Crew returned an empty result.")
                return result_text
            except Exception as exc:
                log(f"[FAIL] {stage_name} attempt {attempt}: {exc}")
                if attempt == self.max_retries:
                    raise RuntimeError(
                        f"Stage '{stage_name}' failed after {self.max_retries} attempts."
                    ) from exc

                delay_seconds = self.base_delay_seconds * (2 ** (attempt - 1))
                log(f"[RETRY] {stage_name} retrying in {delay_seconds} second(s)")
                time.sleep(delay_seconds)

        raise RuntimeError(f"Stage '{stage_name}' did not complete.")

    def run(self, user_input: str) -> Dict[str, str]:
        checkpoint = load_checkpoint(self.checkpoint_path)
        results: Dict[str, str] = {}

        log("[PIPELINE] starting credibility pipeline")
        log(f"[CLAIM] {user_input}")
        checkpoint_claim = checkpoint.get(CHECKPOINT_INPUT_KEY, "")
        completed_stage_names = [
            stage_name for stage_name in STAGE_NAMES if stage_name in checkpoint
        ]

        if checkpoint and checkpoint_claim == user_input:
            if completed_stage_names:
                completed = ", ".join(completed_stage_names)
                log(f"[CHECKPOINT] loaded completed stages for matching claim: {completed}")
                for stage_name in completed_stage_names:
                    results[stage_name] = checkpoint[stage_name]
            else:
                log("[CHECKPOINT] found matching claim but no completed stages")
        elif checkpoint and checkpoint_claim:
            log("[CHECKPOINT] saved claim does not match current input; starting fresh run")
            checkpoint = {CHECKPOINT_INPUT_KEY: user_input}
            save_checkpoint(self.checkpoint_path, checkpoint)
        elif checkpoint:
            log("[CHECKPOINT] legacy checkpoint missing input claim; starting fresh run")
            checkpoint = {CHECKPOINT_INPUT_KEY: user_input}
            save_checkpoint(self.checkpoint_path, checkpoint)
        else:
            log("[CHECKPOINT] no existing checkpoint found")
            checkpoint = {CHECKPOINT_INPUT_KEY: user_input}
            save_checkpoint(self.checkpoint_path, checkpoint)

        stages: List[Dict[str, Any]] = [
            {
                "name": "intake",
                "crew_factory": get_intake_crew,
                "build_inputs": lambda current_results: {"raw_input": user_input},
            },
            {
                "name": "evaluation",
                "crew_factory": get_evaluation_crew,
                "build_inputs": lambda current_results: {
                    "intake_result": current_results["intake"]
                },
            },
            {
                "name": "reporting",
                "crew_factory": get_reporting_crew,
                "build_inputs": lambda current_results: {
                    "intake_result": current_results["intake"],
                    "evaluation_result": current_results["evaluation"],
                },
            },
        ]

        for stage in stages:
            stage_name = stage["name"]

            if stage_name in results:
                log(f"[SKIP] {stage_name} already completed")
                continue

            stage_inputs = stage["build_inputs"](results)
            input_keys = ", ".join(stage_inputs.keys())
            log(f"[START] {stage_name}")
            if stage_name == "intake":
                log(f"[INPUT] {stage_name} claim: {user_input}")
            else:
                log(f"[INPUT] {stage_name} keys: {input_keys}")
            stage_result = self.run_stage(
                stage_name=stage_name,
                crew_factory=stage["crew_factory"],
                inputs=stage_inputs,
            )
            results[stage_name] = stage_result
            checkpoint[stage_name] = stage_result
            save_checkpoint(self.checkpoint_path, checkpoint)
            log(f"[DONE] {stage_name}")
            log(f"[CHECKPOINT] saved {stage_name} to {self.checkpoint_path}")

        log("[PIPELINE] completed credibility pipeline")
        return results


def main() -> int:
    if len(sys.argv) < 2 or not " ".join(sys.argv[1:]).strip():
        log('Usage: python pipeline.py "topic, claim, or article text"')
        return 1

    user_input = " ".join(sys.argv[1:]).strip()
    pipeline = OrchestrationPipeline()
    results = pipeline.run(user_input)

    log("\nFinal executive report:")
    log(results["reporting"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
