from typing import List, Optional
from openenv.core.env_server import Action, Observation, State


class ConfigDebugAction(Action):
    """Action: the agent submits a fixed configuration file"""
    fixed_config: str  # The corrected configuration file content


class ConfigDebugObservation(Observation):
    """Observation: what the agent sees.
    Inherits done: bool, reward: Optional[float], metadata from Observation.
    """
    broken_config: str = ""
    file_type: str = ""
    error_message: str = ""
    task_id: str = ""
    task_description: str = ""
    difficulty: str = ""
    num_bugs: int = 0
    bugs_found_so_far: int = 0
    previous_reward: float = 0.0


class ConfigDebugState(State):
    """Full environment state.
    Inherits episode_id: Optional[str], step_count: int from State.
    """
    current_task_id: str = ""
    current_step: int = 0
    max_steps: int = 5
    total_reward: float = 0.0
    is_done: bool = False
    tasks_completed: List[str] = []
    tasks_remaining: List[str] = []
    
    # Enhanced state fields for better RL signal
    bugs_found_so_far: int = 0
    current_error_message: Optional[str] = None
    progress_ratio: float = 0.0
    current_difficulty: Optional[str] = None
