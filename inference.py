"""
Inference Script - ConfigDebugEnv
===================================
STDOUT FORMAT - emits [START], [STEP], [END] PER TASK:
    [START] task=<task_id> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import asyncio
import os
import sys
import textwrap
from typing import List, Optional

from openai import OpenAI

MAX_STEPS_PER_TASK = 5
TEMPERATURE = 0.1
MAX_TOKENS = 2000

SYSTEM_PROMPT = textwrap.dedent("""
    You are an expert DevOps engineer specializing in configuration file debugging.
    You will be given a broken configuration file and must fix ALL bugs in it.
    Return ONLY the fixed configuration file content.
    No explanations, no markdown formatting, no code blocks. Just the raw fixed configuration.
""").strip()


def clamp(v: float) -> float:
    return max(0.01, min(0.99, v))


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    print(f"[STEP] step={step} action={action} reward={clamp(reward):.2f} done={str(done).lower()} error={error or 'null'}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    s = clamp(score)
    rs = ",".join(f"{clamp(r):.2f}" for r in rewards) if rewards else "0.01"
    print(f"[END] success={str(success).lower()} steps={steps} score={s:.3f} rewards={rs}", flush=True)


def strip_code_blocks(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        text = "\n".join(lines)
    return text


def get_obs_field(data: dict, field: str, default=None):
    """Get field from response - handles both nested and flat formats."""
    obs = data.get("observation", data)
    return obs.get(field, data.get(field, default))


def get_model_fix(client, obs_data, step, history, model_name):
    file_type = get_obs_field(obs_data, "file_type", "config")
    desc = get_obs_field(obs_data, "task_description", "")
    difficulty = get_obs_field(obs_data, "difficulty", "")
    num_bugs = get_obs_field(obs_data, "num_bugs", 0)
    bugs_found = get_obs_field(obs_data, "bugs_found_so_far", 0)
    error_msg = get_obs_field(obs_data, "error_message", "")
    broken = get_obs_field(obs_data, "broken_config", "")

    history_block = "\n".join(history[-4:]) if history else "None"
    prompt = f"""Fix the following broken {file_type} configuration file.

Task: {desc}
Difficulty: {difficulty}
Number of bugs to find: {num_bugs}
Bugs fixed so far: {bugs_found}
Error message: {error_msg}
Step: {step}

Previous attempts:
{history_block}

Broken configuration:
{broken}

Return ONLY the fixed configuration file content."""

    try:
        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return strip_code_blocks(text) if text else ""
    except Exception as e:
        print(f"[DEBUG] LLM error: {e}", flush=True)
        return ""


class HTTPEnvClient:
    def __init__(self, base_url):
        import httpx
        self.base_url = base_url.rstrip("/")
        self.http = httpx.AsyncClient(timeout=60.0)

    async def reset(self):
        r = await self.http.post(f"{self.base_url}/reset")
        r.raise_for_status()
        return r.json()

    async def step(self, fixed_config: str):
        """Send step with correct OpenEnv format: {"action": {"fixed_config": "..."}}"""
        r = await self.http.post(
            f"{self.base_url}/step",
            json={"action": {"fixed_config": fixed_config}},
        )
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self.http.aclose()


async def main():
    api_key = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or ""
    api_base_url = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
    model_name = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
    benchmark = "config_debug_env"

    client = OpenAI(base_url=api_base_url, api_key=api_key)
    env_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:7860"
    env = HTTPEnvClient(env_url)

    try:
        result = await env.reset()
        current_task = get_obs_field(result, "task_id", "unknown")
        task_step = 0
        task_rewards = []
        task_history = []

        log_start(task=current_task, env=benchmark, model=model_name)

        for global_step in range(1, 50):
            fixed_config = get_model_fix(client, result, task_step + 1, task_history, model_name)
            task_step += 1

            try:
                step_result = await env.step(fixed_config)
            except Exception as step_err:
                print(f"[DEBUG] Step failed: {step_err}", flush=True)
                log_step(task_step, f"fix({current_task})", 0.01, False, str(step_err))
                task_rewards.append(0.01)
                # End this task on step failure
                log_end(False, task_step, 0.01, task_rewards)
                break

            reward = get_obs_field(step_result, "reward", 0.01)
            if reward is None:
                reward = 0.01
            reward = clamp(float(reward))
            task_rewards.append(reward)

            new_task = get_obs_field(step_result, "task_id", current_task)
            is_done = get_obs_field(step_result, "done", False)
            error = get_obs_field(step_result, "error_message", None)
            if error == "All checks passed!":
                error = None

            log_step(task_step, f"fix({current_task})", reward, bool(is_done), error)
            task_history.append(f"Step {task_step}: reward {reward:.2f}")

            # Detect task transition
            task_changed = (new_task != current_task) and (new_task != "unknown")

            if task_changed or is_done:
                # End current task
                task_score = clamp(sum(task_rewards) / len(task_rewards)) if task_rewards else 0.01
                log_end(task_score >= 0.5, task_step, task_score, task_rewards)

                if is_done:
                    break

                # Start next task
                current_task = new_task
                task_step = 0
                task_rewards = []
                task_history = []
                log_start(task=current_task, env=benchmark, model=model_name)

            result = step_result

    except Exception as e:
        print(f"[DEBUG] Fatal error: {e}", flush=True)
        log_end(False, 0, 0.01, [0.01])
    finally:
        try:
            await env.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:
        print("[END] success=false steps=0 score=0.01 rewards=0.01", flush=True)