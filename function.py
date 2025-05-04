# worker.py
import redis
import json
import time
import os
import uuid
from dotenv import load_dotenv
from agents.main import main  # Import your main function

# Load environment variables
load_dotenv()

# Connect to Redis (Render provides Redis as an add-on)
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
r = redis.from_url(redis_url)

# Function to process tasks
def process_task(task_id, user_data):
    # Update status to "processing"
    r.set(f"task:{task_id}:status", "processing")
    
    try:
        # Call your main function with the user data
        results = main(user_data)
        
        # Store result and update status
        r.set(f"task:{task_id}:result", json.dumps(results))
        r.set(f"task:{task_id}:status", "completed")
    except Exception as e:
        # Handle errors
        error_message = str(e)
        r.set(f"task:{task_id}:error", error_message)
        r.set(f"task:{task_id}:status", "failed")

# Main worker loop
def worker_loop():
    print("Worker started")
    while True:
        # Check for new tasks
        task = r.blpop("task_queue", timeout=1)
        if task:
            _, task_data = task
            task_data = json.loads(task_data)
            task_id = task_data.get("id")
            user_data = task_data.get("user_data", {})
            
            print(f"Processing task {task_id}")
            process_task(task_id, user_data)
        
        time.sleep(0.1)  # Prevent CPU hogging

if __name__ == "__main__":
    worker_loop()