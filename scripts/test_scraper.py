import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def create_job(url, goal):
    print(f"--- Creating Job ---")
    print(f"URL: {url}")
    print(f"Goal: {goal}")
    
    payload = {
        "url": url,
        "goal": goal
    }
    
    try:
        response = requests.post(f"{BASE_URL}/scrape", json=payload)
        response.raise_for_status()
        data = response.json()
        job_id = data["job_id"]
        print(f"Job created successfully. ID: {job_id}")
        return job_id
    except Exception as e:
        print(f"Error creating job: {e}")
        return None

def poll_job(job_id, timeout=300, interval=10):
    print(f"--- Polling Job {job_id} ---")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{BASE_URL}/status/{job_id}")
            response.raise_for_status()
            data = response.json()
            
            status = data.get("status")
            thought = data.get("thought", "Waiting for agent...")
            
            print(f"[{int(time.time() - start_time)}s] Status: {status}")
            if thought:
                print(f"   Thought: {thought}")
                
            if status == "COMPLETED":
                print("\n--- JOB COMPLETED ---")
                print("Result:")
                print(json.dumps(data.get("result"), indent=2))
                return True
            elif status == "FAILED":
                print("\n--- JOB FAILED ---")
                print(f"Error: {data.get('error')}")
                return False
                
        except Exception as e:
            print(f"Error polling job: {e}")
            break
            
        time.sleep(interval)
    
    print("Polling timed out.")
    return False

if __name__ == "__main__":
    target_url = "https://www.google.com"
    target_goal = "Search for 'Python' and tell me the title of the first search result."
    
    if len(sys.argv) > 2:
        target_url = sys.argv[1]
        target_goal = sys.argv[2]
    
    job_id = create_job(target_url, target_goal)
    if job_id:
        poll_job(job_id)
