import requests
import json
import time

BASE_URL = "http://localhost:8000"

def run_example(url, goal):
    print(f"--- Running Example ---")
    print(f"URL: {url}")
    print(f"Goal: {goal}")
    
    # 1. Create Job
    response = requests.post(f"{BASE_URL}/scrape", json={"url": url, "goal": goal})
    job_id = response.json()["job_id"]
    print(f"Job ID: {job_id}")

    # 2. Poll Status
    while True:
        status_resp = requests.get(f"{BASE_URL}/status/{job_id}")
        data = status_resp.json()
        status = data["status"]
        thought = data.get("thought", "Thinking...")
        
        print(f"Status: {status} | Thought: {thought[:100]}...")
        
        if status == "COMPLETED":
            print("\nRESULT FOUND:")
            print(json.dumps(data["result"], indent=2))
            break
        elif status == "FAILED":
            print(f"\nJOB FAILED: {data.get('error')}")
            break
            
        time.sleep(5)

if __name__ == "__main__":
    run_example(
        "http://books.toscrape.com/", 
        "Find the price of the book 'A Light in the Attic'."
    )
