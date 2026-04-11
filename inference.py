"""
Inference Script — ConfigDebugEnv
===================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
    IMAGE_NAME     The name of the local image to use for the environment if you are using
                   from_docker_image() method

STDOUT FORMAT
- The script emits exactly three line types to stdout:
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import asyncio
import os
import textwrap
from typing import List, Optional

from openai import OpenAI

# Constants (not env-dependent)
IMAGE_NAME = None  # Will be read at runtime
TASK_NAME = "config-debug"  # Default
BENCHMARK = "config_debug_env"  # Default
MAX_STEPS = 35  # 7 tasks × 5 steps each
TEMPERATURE = 0.1
MAX_TOKENS = 2000
SUCCESS_SCORE_THRESHOLD = 0.5  # normalized score in [0, 1]
MAX_TOTAL_REWARD = 7.0  # 7 tasks, 1.0 max per task

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert DevOps engineer specializing in configuration file debugging.
    You will be given a broken configuration file and must fix ALL bugs in it.
    Return ONLY the fixed configuration file content.
    No explanations, no markdown formatting, no code blocks. Just the raw fixed configuration.
    """
).strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


def strip_code_blocks(text: str) -> str:
    """Remove markdown code blocks if LLM wraps output in them."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines)
    return text


def build_user_prompt(obs: dict, step: int, history: List[str]) -> str:
    history_block = "\n".join(history[-4:]) if history else "None"
    return textwrap.dedent(
        f"""
        Fix the following broken {obs['file_type']} configuration file.

        Task: {obs['task_description']}
        Difficulty: {obs['difficulty']}
        Number of bugs to find: {obs['num_bugs']}
        Bugs fixed so far: {obs['bugs_found_so_far']}
        Error message: {obs['error_message']}
        Step: {step}

        Previous attempts:
        {history_block}

        Broken configuration:
        ```
        {obs['broken_config']}
        ```

        Return ONLY the fixed configuration file content.
        """
    ).strip()


def get_model_message(client: OpenAI, obs: dict, step: int, history: List[str], model_name: str) -> str:
    user_prompt = build_user_prompt(obs, step, history)
    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return strip_code_blocks(text) if text else ""
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return ""


async def main() -> None:
    # Use strict os.environ[] reads for API credentials (validator requirement)
    # This ensures no fallback paths or proxy bypass
    api_key = os.environ["API_KEY"]
    api_base_url = os.environ["API_BASE_URL"]
    model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
    task_name = os.getenv("CONFIG_DEBUG_TASK", "config-debug")
    benchmark = os.getenv("CONFIG_DEBUG_BENCHMARK", "config_debug_env")

    client = OpenAI(base_url=api_base_url, api_key=api_key)

    # Connect to the environment via HTTP
    import httpx
    import sys

    class HTTPEnvClient:
        """Simple HTTP client that mimics the OpenEnv SDK interface."""

        def __init__(self, base_url: str):
            self.base_url = base_url.rstrip("/")
            self.http = httpx.AsyncClient(timeout=60.0)

        async def reset(self):
            resp = await self.http.post(f"{self.base_url}/reset")
            resp.raise_for_status()
            return resp.json()

        async def step(self, action_data: dict):
            resp = await self.http.post(f"{self.base_url}/step", json=action_data)
            resp.raise_for_status()
            return resp.json()

        async def close(self):
            await self.http.aclose()

    env_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:7860"
    env = HTTPEnvClient(env_url)

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=benchmark, model=model_name)

    try:
        result = await env.reset()
        obs = result["observation"]
        state = result["state"]

        step_num = 0
        while not state["is_done"]:
            step_num += 1

            fixed_config = get_model_message(client, obs, step_num, history, model_name)

            step_result = await env.step({"fixed_config": fixed_config})
            obs = step_result["observation"]
            state = step_result["state"]
            reward = step_result.get("reward", 0.0)
            done = state["is_done"]
            info = step_result.get("info", {})
            error = info.get("error_message") if info.get("error_message") != "All checks passed!" else None

            rewards.append(reward)
            steps_taken = step_num

            action_summary = f"fix({info.get('task_id', 'unknown')})"
            log_step(step=step_num, action=action_summary, reward=reward, done=done, error=error)

            history.append(f"Step {step_num}: {action_summary} -> reward {reward:+.2f}")

            if done:
                break

        score = sum(rewards) / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[END] success=false error={str(e)}", flush=True)