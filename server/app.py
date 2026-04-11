"""FastAPI application for ConfigDebugEnv.

Uses OpenEnv's create_fastapi_app() for standard framework compatibility
(WebSocket sessions, standard endpoints, grader discovery).
"""
import json
import gradio as gr

from openenv.core.env_server import create_fastapi_app
from server.models import ConfigDebugAction, ConfigDebugObservation, ConfigDebugState
from server.config_debug_environment import ConfigDebugEnvironment
from server.tasks.task_registry import get_task, TASK_ORDER

# ---- Create the standard OpenEnv FastAPI app ----
# create_fastapi_app expects a callable (factory) that returns an Environment
app = create_fastapi_app(
    ConfigDebugEnvironment,       # factory / class — called per session
    ConfigDebugAction,            # action model (inherits Action)
    ConfigDebugObservation,       # observation model (inherits Observation)
)




# ---- Custom endpoints ----

@app.get("/info")
def info():
    return {"name": "ConfigDebugEnv", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}





@app.get("/tasks")
def tasks():
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


# ---- Gradio Web UI ----

_ui_env = ConfigDebugEnvironment()


def format_state(env):
    """Format environment state with progress bar and RL signals."""
    state = env.state
    progress_bar = "█" * int(state.progress_ratio * 10) + "░" * (10 - int(state.progress_ratio * 10))
    
    return f"""
Task Progress: {len(state.tasks_completed)+1}/7
Progress: {progress_bar} ({int(state.progress_ratio*100)}%)
Total Reward: {state.total_reward:.2f}

Current Task: {state.current_task_id}
Difficulty: {state.current_difficulty}

Bugs Found: {state.bugs_found_so_far}
Error: {state.current_error_message or 'None'}

Completed: {', '.join(state.tasks_completed) if state.tasks_completed else 'None'}
Remaining: {', '.join(state.tasks_remaining[:3]) if state.tasks_remaining else 'None'}
"""


def ui_get_state():
    """Get current environment state (inspectable state)."""
    return format_state(_ui_env)


def ui_reset():
    _ui_env.reset()
    obs = _ui_env._build_observation()
    return (
        f"Task: {obs.task_id} | Difficulty: {obs.difficulty} | Bugs: {obs.num_bugs}",
        obs.task_description,
        obs.broken_config,
        obs.error_message,
        format_state(_ui_env),
        "Environment reset. Submit a fixed config to begin.",
    )


def ui_step(fixed_config):
    if _ui_env._done:
        return (
            "All tasks completed!",
            "",
            "",
            "Episode done. Click Reset to start again.",
            format_state(_ui_env),
            f"Final score: {_ui_env.total_reward:.1f} / {len(TASK_ORDER)}.0",
        )

    action = ConfigDebugAction(fixed_config=fixed_config)
    obs = _ui_env.step(action)

    history = f"Reward: {obs.reward:.2f} | Bugs found: {obs.bugs_found_so_far}/{obs.num_bugs}\nFeedback: {obs.error_message}"
    return (
        f"Task: {obs.task_id} | Difficulty: {obs.difficulty} | Bugs: {obs.num_bugs}",
        obs.task_description,
        obs.broken_config,
        obs.error_message,
        format_state(_ui_env),
        history,
    )


with gr.Blocks(title="ConfigDebugEnv") as demo:
    gr.Markdown("# ConfigDebugEnv")
    gr.Markdown("An RL environment for debugging broken config files across 7 real-world formats.")

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Agent Interface")
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
            state_display = gr.Textbox(label="Current State (with RL Signals)", interactive=False, lines=14)
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


def main(host: str = "0.0.0.0", port: int = 7860):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
