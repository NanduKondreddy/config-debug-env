from server.config_debug_environment import ConfigDebugEnvironment
from server.models import ConfigDebugAction
from server.tasks.task_registry import get_task

env = ConfigDebugEnvironment()

# ONLY ONE RESET
obs = env.reset()

for i in range(3):
    print(f"\n--- Step {i+1} ---")

    task = get_task(obs.task_id)
    correct_output = task.ground_truth

    action = ConfigDebugAction(fixed_config=correct_output)
    obs = env.step(action)

    print("Task ID:", obs.task_id)
    print("Reward:", obs.reward)
    print("Done:", obs.done)