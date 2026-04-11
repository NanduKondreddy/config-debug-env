from fastapi import FastAPI, HTTPException
from typing import Optional
import json
import gradio as gr

from server.models import ConfigDebugAction, ConfigDebugObservation, ConfigDebugState
from server.tasks.task_registry import get_task, get_all_task_ids, TASK_ORDER

app = FastAPI(title="ConfigDebugEnv", version="1.0.0")

# --- Environment State ---
MAX_STEPS_PER_TASK = 5


class EnvironmentState:
    """Mutable environment state that persists across requests."""

    def __init__(self):
        self.reset_state()

    def reset_state(self):
        self.task_ids = list(TASK_ORDER)
        self.current_task_index = 0
        self.current_step = 0
        self.total_reward = 0.0
        self.is_done = False
        self.tasks_completed = []
        self.bugs_found_so_far = 0
        self.previous_reward = 0.0
        self.current_error_message: Optional[str] = None
        self.current_broken_config: Optional[str] = None


env_state = EnvironmentState()


def _get_current_task_id() -> str:
    if env_state.current_task_index < len(env_state.task_ids):
        return env_state.task_ids[env_state.current_task_index]
    return env_state.task_ids[-1]


def _build_observation() -> ConfigDebugObservation:
    task_id = _get_current_task_id()
    task = get_task(task_id)

    broken_config = (
        env_state.current_broken_config
        if env_state.current_broken_config is not None
        else task.broken_config
    )
    error_message = (
        env_state.current_error_message
        if env_state.current_error_message is not None
        else task.error_message
    )

    return ConfigDebugObservation(
        broken_config=broken_config,
        file_type=task.file_type,
        error_message=error_message,
        task_id=task.task_id,
        task_description=task.description,
        difficulty=task.difficulty,
        num_bugs=task.num_bugs,
        bugs_found_so_far=env_state.bugs_found_so_far,
        previous_reward=env_state.previous_reward,
    )


def _build_state() -> ConfigDebugState:
    task_id = _get_current_task_id()
    tasks_remaining = env_state.task_ids[env_state.current_task_index:]
    if env_state.is_done:
        tasks_remaining = []

    return ConfigDebugState(
        current_task_id=task_id,
        current_step=env_state.current_step,
        max_steps=MAX_STEPS_PER_TASK,
        total_reward=round(env_state.total_reward, 4),
        is_done=env_state.is_done,
        tasks_completed=list(env_state.tasks_completed),
        tasks_remaining=tasks_remaining,
    )


# --- API Endpoints ---


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/info")
def info():
    return {"name": "ConfigDebugEnv", "version": "1.0.0", "status": "running"}


@app.post("/reset")
def reset(task_id: str = None):
    """Reset the environment to initial state, return first observation."""
    env_state.reset_state()
    if task_id and task_id in env_state.task_ids:
        env_state.current_task_index = env_state.task_ids.index(task_id)

    observation = _build_observation()
    state = _build_state()

    return {
        "observation": observation.model_dump(),
        "state": state.model_dump(),
    }


@app.post("/step")
def step(action: ConfigDebugAction):
    """
    Take a step in the environment.
    The agent submits a fixed config, the grader evaluates it.
    """
    if env_state.is_done:
        raise HTTPException(
            status_code=400,
            detail="Environment is done. Call /reset to start a new episode.",
        )

    task_id = _get_current_task_id()
    task = get_task(task_id)

    # Run the grader
    reward, error_message, bugs_fixed = task.grader(action.fixed_config)
    reward = max(0.01, min(0.99, reward))

    env_state.current_step += 1
    env_state.bugs_found_so_far = len(bugs_fixed)
    env_state.previous_reward = round(reward, 4)

    # Update error message for feedback
    env_state.current_error_message = error_message

    # Check if task is complete (perfect score or max steps reached)
    task_done = reward >= 0.99 or env_state.current_step >= MAX_STEPS_PER_TASK

    task_reward = reward  # Reward for this step

    if task_done:
        # Record the best reward for this task
        env_state.total_reward += reward
        env_state.tasks_completed.append(task_id)
        env_state.current_task_index += 1

        # Reset per-task state
        env_state.current_step = 0
        env_state.bugs_found_so_far = 0
        env_state.current_error_message = None
        env_state.current_broken_config = None

        # Check if all tasks are done
        if env_state.current_task_index >= len(env_state.task_ids):
            env_state.is_done = True
    else:
        # If the agent submitted something, use it as the new "broken" config
        # so the agent can iterate
        env_state.current_broken_config = action.fixed_config

    observation = _build_observation()
    state = _build_state()

    return {
        "observation": observation.model_dump(),
        "reward": round(task_reward, 4),
        "done": env_state.is_done,
        "state": state.model_dump(),
        "info": {
            "task_id": task_id,
            "bugs_fixed": bugs_fixed,
            "error_message": error_message,
            "task_done": task_done,
        },
    }


@app.get("/state")
def state():
    """Return current environment state."""
    return _build_state().model_dump()


@app.get("/observation")
def observation():
    """Return current observation."""
    if env_state.is_done:
        raise HTTPException(
            status_code=400,
            detail="Environment is done. Call /reset to start a new episode.",
        )
    return _build_observation().model_dump()



@app.get("/metadata")
def metadata():
    return {
        "env_name": "config_debug_env",
        "version": "1.0.0",
        "description": "Config file debugging environment",
        "tasks": [
            {"id": "task1_json", "name": "JSON Config Debug", "difficulty": "easy", "num_bugs": 2, "has_grader": True, "grader": "server.graders.json_grader:grade_task1"},
            {"id": "task2_yaml", "name": "YAML Config Debug", "difficulty": "easy", "num_bugs": 2, "has_grader": True, "grader": "server.graders.yaml_grader:grade_task2"},
            {"id": "task3_dockerfile", "name": "Dockerfile Debug", "difficulty": "medium", "num_bugs": 3, "has_grader": True, "grader": "server.graders.dockerfile_grader:grade_task3"},
            {"id": "task4_compose", "name": "Docker Compose Debug", "difficulty": "medium", "num_bugs": 4, "has_grader": True, "grader": "server.graders.compose_grader:grade_task4"},
            {"id": "task5_k8s", "name": "Kubernetes Config Debug", "difficulty": "hard", "num_bugs": 5, "has_grader": True, "grader": "server.graders.k8s_grader:grade_task5"},
            {"id": "task6_github_actions", "name": "GitHub Actions Debug", "difficulty": "hard", "num_bugs": 5, "has_grader": True, "grader": "server.graders.github_actions_grader:grade_task6"},
            {"id": "task7_nginx", "name": "Nginx Config Debug", "difficulty": "very_hard", "num_bugs": 6, "has_grader": True, "grader": "server.graders.nginx_grader:grade_task7"},
        ],
        "action_model": "ConfigDebugAction",
        "observation_model": "ConfigDebugObservation",
        "state_model": "ConfigDebugState",
    }


@app.get("/tasks")
def tasks():
    """Return list of all tasks with grader information."""
    return {
        "tasks": [
            {
                "id": tid,
                "name": get_task(tid).description,
                "difficulty": get_task(tid).difficulty,
                "file_type": get_task(tid).file_type,
                "num_bugs": get_task(tid).num_bugs,
                "has_grader": True,
            }
            for tid in TASK_ORDER
        ],
        "total_tasks": len(TASK_ORDER),
        "tasks_with_graders": len(TASK_ORDER),
    }

@app.get("/schema")
def schema():
    return {
        "action": ConfigDebugAction.model_json_schema(),
        "observation": ConfigDebugObservation.model_json_schema(),
        "state": ConfigDebugState.model_json_schema(),
    }

# --- Gradio Web UI ---


def ui_reset():
    env_state.reset_state()
    obs = _build_observation()
    st = _build_state()
    return (
        f"Task: {obs.task_id} | Difficulty: {obs.difficulty} | Bugs: {obs.num_bugs}",
        obs.task_description,
        obs.broken_config,
        obs.error_message,
        json.dumps(st.model_dump(), indent=2),
        "Environment reset. Submit a fixed config to begin.",
    )


def ui_step(fixed_config):
    if env_state.is_done:
        st = _build_state()
        return (
            "All tasks completed!",
            "",
            "",
            "Episode done. Click Reset to start again.",
            json.dumps(st.model_dump(), indent=2),
            f"Final score: {env_state.total_reward:.1f} / {len(TASK_ORDER)}.0",
        )

    task_id = _get_current_task_id()
    task = get_task(task_id)
    reward, error_message, bugs_fixed = task.grader(fixed_config)
    reward = max(0.01, min(0.99, reward))

    env_state.current_step += 1
    env_state.bugs_found_so_far = len(bugs_fixed)
    env_state.previous_reward = round(reward, 4)
    env_state.current_error_message = error_message

    task_done = reward >= 0.99 or env_state.current_step >= MAX_STEPS_PER_TASK

    if task_done:
        env_state.total_reward += reward
        env_state.tasks_completed.append(task_id)
        env_state.current_task_index += 1
        env_state.current_step = 0
        env_state.bugs_found_so_far = 0
        env_state.current_error_message = None
        env_state.current_broken_config = None
        if env_state.current_task_index >= len(env_state.task_ids):
            env_state.is_done = True
    else:
        env_state.current_broken_config = fixed_config

    obs = _build_observation()
    st = _build_state()
    history = f"Reward: {reward:.2f} | Bugs fixed: {bugs_fixed} | Task done: {task_done}\nFeedback: {error_message}"

    return (
        f"Task: {obs.task_id} | Difficulty: {obs.difficulty} | Bugs: {obs.num_bugs}",
        obs.task_description,
        obs.broken_config,
        obs.error_message,
        json.dumps(st.model_dump(), indent=2),
        history,
    )


def ui_get_state():
    st = _build_state()
    return json.dumps(st.model_dump(), indent=2)


with gr.Blocks(title="ConfigDebugEnv", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ConfigDebugEnv")
    gr.Markdown("An RL environment for debugging broken config files across 7 real-world formats: JSON, YAML, Dockerfile, docker-compose, Kubernetes, GitHub Actions, nginx.")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### HumanAgent Interface")
            task_info = gr.Textbox(label="Current Task", interactive=False)
            task_desc = gr.Textbox(label="Task Description", interactive=False, lines=2)
            broken_config = gr.Textbox(label="Broken Config", interactive=False, lines=10)
            error_msg = gr.Textbox(label="Error Message", interactive=False, lines=2)

            gr.Markdown("### Take Action")
            fixed_config_input = gr.Textbox(label="Your Fixed Config", placeholder="Paste your fixed configuration here...", lines=10)
            with gr.Row():
                reset_btn = gr.Button("Reset Environment", variant="secondary")
                step_btn = gr.Button("Step", variant="primary")
                state_btn = gr.Button("Get State", variant="secondary")

        with gr.Column(scale=1):
            gr.Markdown("### State Observer")
            state_display = gr.Textbox(label="Current State", interactive=False, lines=12)
            history_display = gr.Textbox(label="Action History / Reward", interactive=False, lines=4)

    reset_btn.click(
        fn=ui_reset,
        outputs=[task_info, task_desc, broken_config, error_msg, state_display, history_display],
    )
    step_btn.click(
        fn=ui_step,
        inputs=[fixed_config_input],
        outputs=[task_info, task_desc, broken_config, error_msg, state_display, history_display],
    )
    state_btn.click(
        fn=ui_get_state,
        outputs=[state_display],
    )

app = gr.mount_gradio_app(app, demo, path="/")
