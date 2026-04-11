"""ConfigDebugEnvironment - OpenEnv-compatible environment class.

Inherits from openenv.core.env_server.Environment and implements
the standard reset/step/state interface with multi-task logic.
"""
import asyncio
import os
import textwrap
from typing import Optional, Any
from uuid import uuid4

from openai import OpenAI
from openenv.core.env_server import Environment
from server.models import ConfigDebugAction, ConfigDebugObservation, ConfigDebugState
from server.tasks.task_registry import get_task, TASK_ORDER

MAX_STEPS_PER_TASK = 5

# LLM Configuration (same as inference.py)
SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an expert DevOps/Infrastructure engineer specializing in configuration file debugging.
    
    Your task: Fix ALL bugs in the provided configuration file.
    
    CRITICAL RULES:
    1. Analyze the error message carefully - it identifies the exact problems
    2. Fix EVERY bug mentioned in "Number of bugs to find"
    3. Preserve exact formatting and indentation from the original (except fixes)
    4. Validate syntax BEFORE returning - no invalid XML/JSON/YAML
    5. Return ONLY the fixed configuration file content - absolutely no explanations or comments
    6. Keep identical all lines that have no bugs
    7. If there are multiple bugs, fix them ALL in one response
    
    SUCCESS CRITERIA: Your output must pass syntax validation and fix all identified bugs.
    """
).strip()

TEMPERATURE = 0.0
MAX_TOKENS = 4000


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


async def generate_fix_async(observation: ConfigDebugObservation, step: int = 1) -> str:
    """
    Call LLM agent to generate a fix for the current task.
    Returns the fixed configuration string.
    """
    # Read API credentials (strict env reads like inference.py)
    try:
        api_key = os.environ["API_KEY"]
        api_base_url = os.environ["API_BASE_URL"]
    except KeyError as e:
        print(f"[LLM AGENT] Missing env var: {e}", flush=True)
        return ""
    
    # Get model name
    model_name = os.getenv("MODEL_NAME", "gpt-4o")
    
    # Create client
    client = OpenAI(base_url=api_base_url, api_key=api_key)
    
    # Build prompt
    user_prompt = textwrap.dedent(
        f"""
        FILE TYPE: {observation.file_type.upper()}
        TASK: {observation.task_description}
        DIFFICULTY: {observation.difficulty}
        TOTAL BUGS TO FIX: {observation.num_bugs}
        BUGS FIXED SO FAR: {observation.bugs_found_so_far} of {observation.num_bugs}
        CURRENT ERROR: {observation.error_message}
        STEP: {step}
        
        THE BROKEN CONFIGURATION:
        {observation.broken_config}
        
        INSTRUCTIONS:
        1. Review the error message above - it tells you exactly what is broken
        2. You have found {observation.bugs_found_so_far} bugs so far, you need to find {observation.num_bugs} - {observation.bugs_found_so_far} more
        3. Fix ALL remaining bugs in a single response
        4. Keep the exact same format/indentation as the original except for the fixes
        5. Output ONLY the corrected configuration file - no markdown, no explanation, no "```"
        6. The fixed configuration MUST be syntactically valid {observation.file_type.upper()}
        """
    ).strip()
    
    try:
        print(f"[LLM AGENT] Calling model={model_name} for task={observation.task_id} step={step}", flush=True)
        
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
        
        fixed_config = (completion.choices[0].message.content or "").strip()
        
        # Clean up code blocks
        fixed_config = strip_code_blocks(fixed_config)
        
        # Remove explanatory prefixes
        if fixed_config.startswith("Here") or fixed_config.startswith("Here's"):
            lines = fixed_config.split("\n")
            for i, line in enumerate(lines):
                if not line.startswith("Here"):
                    fixed_config = "\n".join(lines[i:])
                    break
        
        print(f"[LLM AGENT] Generated fix: {len(fixed_config)} chars, task={observation.task_id}", flush=True)
        return fixed_config
        
    except Exception as e:
        print(f"[LLM AGENT] Error: {e}", flush=True)
        return ""


def generate_fix(observation: ConfigDebugObservation, step: int = 1) -> str:
    """
    Synchronous wrapper to generate fix using async LLM call.
    """
    try:
        return asyncio.run(generate_fix_async(observation, step))
    except RuntimeError as e:
        # If event loop already exists, use get_event_loop
        if "asyncio.run() cannot be called from a running event loop" in str(e):
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(generate_fix_async(observation, step))
        raise


class ConfigDebugEnvironment(Environment):
    """Multi-task config debugging environment.

    Manages 7 sequential tasks internally. Each WebSocket session
    (via create_fastapi_app) gets its own instance with independent state.
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        self._init_episode()

    def _init_episode(self):
        self.task_ids = list(TASK_ORDER)
        self.current_task_index = 0
        self.current_step = 0
        self.total_reward = 0.0
        self._done = False
        self.tasks_completed: list = []
        self.bugs_found_so_far = 0
        self.previous_reward = 0.0
        self.current_error_message: Optional[str] = None
        self.current_broken_config: Optional[str] = None
        self._episode_id = str(uuid4())
        self._global_step = 0

    # ---- OpenEnv interface methods ----

    def reset(self, seed: Optional[int] = None, episode_id: Optional[str] = None, **kwargs: Any) -> ConfigDebugObservation:
        """Reset environment to initial state (task 1)."""
        self._init_episode()
        if episode_id:
            self._episode_id = episode_id
        return self._build_observation()

    def step(self, action: ConfigDebugAction, timeout_s: Optional[float] = None, **kwargs: Any) -> ConfigDebugObservation:
        """Process an action: run the grader, advance tasks if done."""
        if self._done:
            return self._build_observation()

        task_id = self._current_task_id()
        task = get_task(task_id)

        # Check if validator sent empty fixed_config (signal to autonomously solve)
        fc = action.fixed_config
        is_empty_submission = not fc or fc.strip() == ""
        
        print(f"\n[STEP] task={task_id} step={self.current_step + 1} fixed_config_empty={is_empty_submission}", flush=True)
        
        if is_empty_submission:
            # Validator sent empty config - environment must autonomously generate fix
            print(f"[AUTONOMOUS SOLVING] Generating fix for task={task_id}", flush=True)
            obs = self._build_observation()
            fixed_config = generate_fix(obs, step=self.current_step + 1)
            
            if not fixed_config:
                print(f"[AUTONOMOUS SOLVING] ERROR: LLM returned empty fix for task={task_id}", flush=True)
                fixed_config = ""  # Fallback to empty, grader will return 0.001
            else:
                print(f"[AUTONOMOUS SOLVING] Generated {len(fixed_config)} char fix for task={task_id}", flush=True)
        else:
            # Use provided fixed_config
            fixed_config = fc
            print(f"[PROVIDED CONFIG] Using submitted fix: {len(fixed_config)} chars", flush=True)

        # Run the grader (returns float for validator compatibility)
        grader_result = task.grader(fixed_config)
        
        # Convert to internal tuple format (reward, error_msg, bugs_fixed)
        if isinstance(grader_result, tuple):
            reward, error_message, bugs_fixed = grader_result
        else:
            # Grader returns float - convert to tuple
            reward = grader_result
            error_message = ""
            bugs_fixed = []
        
        # DEBUG: Log raw grader output
        print(
            f"[GRADER RESULT] task={task_id} "
            f"reward={reward} "
            f"type={type(reward).__name__} "
            f"bugs_fixed_count={len(bugs_fixed)}",
            flush=True
        )
        
        reward = max(0.0, min(1.0, reward))

        self.current_step += 1
        self._global_step += 1
        self.bugs_found_so_far = len(bugs_fixed)
        self.previous_reward = round(reward, 4)
        self.current_error_message = error_message

        # Check if task is complete
        task_done = reward >= 0.99 or self.current_step >= MAX_STEPS_PER_TASK

        if task_done:
            self.total_reward += reward
            self.tasks_completed.append(task_id)
            self.current_task_index += 1
            self.current_step = 0
            self.bugs_found_so_far = 0
            self.current_error_message = None
            self.current_broken_config = None
            if self.current_task_index >= len(self.task_ids):
                self._done = True
        else:
            self.current_broken_config = action.fixed_config

        obs = self._build_observation()
        obs.done = self._done
        obs.reward = round(reward, 4)
        return obs

    @property
    def state(self) -> ConfigDebugState:
        """Return current environment state with enhanced RL signals."""
        tasks_remaining = self.task_ids[self.current_task_index:]
        if self._done:
            tasks_remaining = []

        total_tasks = len(self.task_ids)
        completed_tasks = len(self.tasks_completed)
        progress_ratio = completed_tasks / total_tasks if total_tasks > 0 else 0.0

        current_task = get_task(self._current_task_id())

        return ConfigDebugState(
            episode_id=self._episode_id,
            step_count=self._global_step,
            current_task_id=self._current_task_id(),
            current_step=self.current_step,
            max_steps=MAX_STEPS_PER_TASK,
            total_reward=round(self.total_reward, 4),
            is_done=self._done,
            tasks_completed=list(self.tasks_completed),
            tasks_remaining=tasks_remaining,
            # Enhanced RL signals
            bugs_found_so_far=self.bugs_found_so_far,
            current_error_message=self.current_error_message,
            progress_ratio=round(progress_ratio, 2),
            current_difficulty=current_task.difficulty,
        )

    # ---- Internal helpers ----

    def _current_task_id(self) -> str:
        if self.current_task_index < len(self.task_ids):
            return self.task_ids[self.current_task_index]
        return self.task_ids[-1]

    def _build_observation(self) -> ConfigDebugObservation:
        task_id = self._current_task_id()
        task = get_task(task_id)
        broken = self.current_broken_config if self.current_broken_config is not None else task.broken_config
        error = self.current_error_message if self.current_error_message is not None else task.error_message

        return ConfigDebugObservation(
            broken_config=broken,
            file_type=task.file_type,
            error_message=error,
            task_id=task.task_id,
            task_description=task.description,
            difficulty=task.difficulty,
            num_bugs=task.num_bugs,
            bugs_found_so_far=self.bugs_found_so_far,
            previous_reward=self.previous_reward,
            done=self._done,
            reward=self.previous_reward,
        )
