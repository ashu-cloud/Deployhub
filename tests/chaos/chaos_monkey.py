import subprocess
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Services that are safe to randomly restart (stateless or designed to recover)
CHAOS_TARGETS = [
    "build-orchestrator-1",
    "project-service-1",
    "deployment-service-1"
]

def get_running_containers():
    result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
    return [name for name in result.stdout.strip().split("\n") if name]

def kill_container(container_name):
    logging.warning(f"CHAOS MONKEY: Killing {container_name}")
    subprocess.run(["docker", "kill", container_name], check=True)
    
def restart_container(container_name):
    logging.info(f"CHAOS MONKEY: Restarting {container_name}")
    subprocess.run(["docker", "start", container_name], check=True)

def run_chaos(duration_seconds=60, interval_seconds=15):
    start_time = time.time()
    while time.time() - start_time < duration_seconds:
        running = get_running_containers()
        valid_targets = [c for c in running if any(t in c for t in CHAOS_TARGETS)]
        
        if valid_targets:
            target = random.choice(valid_targets)
            kill_container(target)
            
            # Wait a few seconds to let the system notice the failure
            time.sleep(5)
            
            restart_container(target)
        else:
            logging.info("No valid targets found to kill.")
            
        time.sleep(interval_seconds)

if __name__ == "__main__":
    logging.info("Starting Chaos Monkey")
    run_chaos(duration_seconds=120, interval_seconds=20)
    logging.info("Chaos Monkey Finished")
