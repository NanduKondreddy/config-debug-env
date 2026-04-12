"""FastAPI application for ConfigDebugEnv.

Uses OpenEnv's create_fastapi_app() for standard framework compatibility
(WebSocket sessions, standard endpoints, grader discovery).
"""
import json
import gradio as gr
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from openenv.core.env_server import create_fastapi_app
from server.models import ConfigDebugAction, ConfigDebugObservation, ConfigDebugState
from server.config_debug_environment import ConfigDebugEnvironment
from server.tasks.task_registry import get_task, TASK_ORDER

# ---- Create the standard OpenEnv FastAPI app ----
app = create_fastapi_app(
    ConfigDebugEnvironment,
    ConfigDebugAction,
    ConfigDebugObservation,
)

# ---- Remove default routes we need to override ----
for i, route in enumerate(app.router.routes):
    if hasattr(route, "path") and route.path == "/reset":
        app.router.routes.pop(i)
        print("[APP_INIT] Removed default /reset route for schema fix")
        break

for i, route in enumerate(app.router.routes):
    if hasattr(route, "path") and route.path == "/metadata":
        app.router.routes.pop(i)
        print("[APP_INIT] Removed default /metadata route for override")
        break

# ---- Middleware to fix /reset response schema ----
class ResetSchemaFixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path == "/reset" and request.method == "POST":
            if response.status_code == 200:
                try:
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk
                    data = json.loads(body)
                    if isinstance(data, dict) and "observation" in data:
                        fixed_data = {
                            "observation": data["observation"],
                            "done": data.get("done", False),
                            "reward": 0.0,
                            "metadata": data.get("metadata", {}),
                            "info": {}
                        }
                        print("[MIDDLEWARE] Fixed /reset response schema - added base fields")
                        return JSONResponse(fixed_data, status_code=200)
                except Exception as e:
                    print(f"[MIDDLEWARE] Error fixing reset response: {e}")
        return response

app.add_middleware(ResetSchemaFixMiddleware)

# ---- Startup Diagnostics ----
print("[APP_INIT] ConfigDebugEnvironment initialization started")
print(f"[APP_INIT] Loaded {len(TASK_ORDER)} tasks: {TASK_ORDER}")
for task_id in TASK_ORDER:
    try:
        task = get_task(task_id)
        print(f"[APP_INIT] Task '{task_id}' loaded: grader={task.grader.__name__}")
    except Exception as e:
        print(f"[APP_INIT] ERROR loading task '{task_id}': {str(e)}")


# ---- Custom endpoints ----

@app.get("/info")
def info():
    return {"name": "ConfigDebugEnv", "version": "1.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/metadata")
def metadata():
    """Metadata endpoint with grader paths for validator discovery."""
    print("[VALIDATOR] GET /metadata called")
    return {
        "name": "ConfigDebugEnvironment",
        "description": "An environment for training AI agents to debug broken configuration files",
        "version": "1.0.0",
        "tasks": [
            {
                "id": tid,
                "has_grader": True,
                "grader": f"server.graders.grader_api:grade_{tid}",
            }
            for tid in TASK_ORDER
        ],
    }


@app.post("/reset")
async def reset_env(request: Request):
    """Override /reset endpoint to return correct OpenEnv contract schema."""
    print("[VALIDATOR] POST /reset called - CUSTOM OVERRIDE")
    try:
        env = ConfigDebugEnvironment()
        observation = env.reset()
        fixed_response = {
            "observation": observation.model_dump(),
            "done": False,
            "reward": 0.0,
            "metadata": {},
            "info": {}
        }
        print("[VALIDATOR] Reset response formatted with base fields")
        return fixed_response
    except Exception as e:
        print(f"[VALIDATOR] Error in custom reset: {e}")
        raise


@app.post("/grader")
async def grader_endpoint(request: Request):
    """Score a submitted config for a specific task without a full episode.
    The validator calls this to verify each task has a working grader
    with scores strictly between 0 and 1."""
    print("[VALIDATOR] POST /grader called")
    try:
        body = await request.json()
        task_id = body.get("task_id", TASK_ORDER[0])
        submitted_config = body.get("submitted_config",
            body.get("action", {}).get("fixed_config", "{}"))

        from server.graders.grader_api import (
            grade_task1, grade_task2, grade_task3,
            grade_task4, grade_task5, grade_task6, grade_task7,
        )

        grader_map = {
            "task1_json": grade_task1,
            "task2_yaml": grade_task2,
            "task3_dockerfile": grade_task3,
            "task4_compose": grade_task4,
            "task5_k8s": grade_task5,
            "task6_github_actions": grade_task6,
            "task7_nginx": grade_task7,
        }

        grader_fn = grader_map.get(task_id)
        if grader_fn is None:
            return {"error": f"Unknown task_id: {task_id}", "score": 0.01}

        score = grader_fn(submitted_config)
        print(f"[GRADER] task={task_id} score={score}")
        return {"task_id": task_id, "score": score, "has_grader": True}
    except Exception as e:
        print(f"[GRADER] Error: {e}")
        return {"error": str(e), "score": 0.01}


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
                "grader": f"server.graders.grader_api:grade_{tid}",
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


# ---- Gradio Web UI ----

_ui_env = ConfigDebugEnvironment()


def format_state(env):
    state = env.state
    progress_bar = "\u2588" * int(state.progress_ratio * 10) + "\u2591" * (10 - int(state.progress_ratio * 10))
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