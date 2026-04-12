"""ConfigDebugEnvironment - OpenEnv-compatible environment class.

Inherits from openenv.core.env_server.Environment and implements
the standard reset/step/state interface with multi-task logic.
"""
from typing import Optional, Any
from uuid import uuid4

from openenv.core.env_server import Environment
from server.models import ConfigDebugAction, ConfigDebugObservation, ConfigDebugState
from server.tasks.task_registry import get_task, TASK_ORDER

MAX_STEPS_PER_TASK = 5


class ConfigDebugEnvironment(Environment):
    """Multi-task config debugging environment.

    Manages 7 sequential tasks internally. Each WebSocket session
    (via create_fastapi_app) gets its own instance with independent state.
    """

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self):
        super().__init__()
        self._init_episode()

    def _init_episode(self):
        self.task_ids = list(TASK_ORDER)
        self.current_task_index = 0
        self.current_step = 0
        self.total_reward = 0.0
        self._done = False
        self.tasks_completed: list = []
        self.bugs_found_so_far = 0
        self.previous_reward = None
        self.current_error_message: Optional[str] = None
        self.current_broken_config: Optional[str] = None
        self._episode_id = str(uuid4())
        self._global_step = 0

    # ---- OpenEnv interface methods ----

    def reset(self, seed: Optional[int] = None, episode_id: Optional[str] = None, **kwargs: Any) -> ConfigDebugObservation:
        """Reset environment. Supports task_id kwarg for per-task validation."""
        self._init_episode()
        if episode_id:
            self._episode_id = episode_id
        
        # Allow validator to reset to a specific task
        task_id = kwargs.get("task_id")
        if task_id and task_id in self.task_ids:
            self.current_task_index = self.task_ids.index(task_id)
        
        return self._build_observation()

    def step(self, action: ConfigDebugAction, timeout_s: Optional[float] = None, **kwargs: Any) -> ConfigDebugObservation:
        """Process an action: run the grader, advance tasks if done."""
        if self._done:
            return self._build_observation()

        task_id = self._current_task_id()
        task = get_task(task_id)

        # Run the grader - returns (reward, error_message, bugs_fixed) tuple
        grader_result = task.grader(action.fixed_config)

        # Parse grader result
        if isinstance(grader_result, tuple) and len(grader_result) >= 3:
            reward = float(grader_result[0])
            error_message = str(grader_result[1])
            bugs_fixed = list(grader_result[2])
        elif isinstance(grader_result, tuple) and len(grader_result) >= 1:
            reward = float(grader_result[0])
            error_message = ""
            bugs_fixed = []
        elif isinstance(grader_result, (int, float)):
            reward = float(grader_result)
            error_message = ""
            bugs_fixed = []
        else:
            reward = 0.01
            error_message = "Grader returned unexpected format"
            bugs_fixed = []

        reward = max(0.01, min(0.90, reward))

        self.current_step += 1
        self._global_step += 1
        self.bugs_found_so_far = len(bugs_fixed)
        self.previous_reward = round(reward, 4)
        self.current_error_message = error_message

        # Check if task is complete
        task_done = reward >= 0.85 or self.current_step >= MAX_STEPS_PER_TASK

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
            ground_truth=task.ground_truth,
            file_type=task.file_type,
            error_message=error,
            task_id=task.task_id,
            task_description=task.description,
            difficulty=task.difficulty,
            num_bugs=task.num_bugs,
            bugs_found_so_far=self.bugs_found_so_far,
            previous_reward=self.previous_reward if self.previous_reward is not None else 0.01,
            done=self._done,
            reward=self.previous_reward,
        )