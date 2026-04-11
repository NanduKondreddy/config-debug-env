"""Client for ConfigDebugEnv - connects to the environment server."""
from typing import Dict, Any

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from server.models import ConfigDebugAction, ConfigDebugObservation, ConfigDebugState


class ConfigDebugEnv(EnvClient[ConfigDebugAction, ConfigDebugObservation, ConfigDebugState]):
    """Typed client for the ConfigDebugEnv environment."""

    def _step_payload(self, action: ConfigDebugAction) -> Dict[str, Any]:
        return {"fixed_config": action.fixed_config}

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[ConfigDebugObservation]:
        obs_data = payload.get("observation", {})
        obs = ConfigDebugObservation(**obs_data)
        return StepResult(
            observation=obs,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> ConfigDebugState:
        return ConfigDebugState(**payload)
