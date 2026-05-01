import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_scrape(url, goal):
    print(f"Submitting job: Scrape {url} with goal '{goal}'")
    
    response = requests.post(f"{BASE_URL}/scrape", json={
        "url": url,
        "goal": goal
    })
    
    if response.status_code != 200:
        print(f"Failed to submit job: {response.text}")
        return
    
    job_id = response.json()["job_id"]
    print(f"Job submitted. ID: {job_id}")
    
    while True:
        status_response = requests.get(f"{BASE_URL}/status/{job_id}")
        data = status_response.json()
        
        status = data["status"]
        thought = data.get("thought", "...")
        
        print(f"Status: {status} | Thought: {thought[:100]}...")
        
        if status in ["COMPLETED", "FAILED"]:
            print("\nFinal Result:")
            if status == "COMPLETED":
                print(data["result"])
            else:
                print(f"Error: {data['error']}")
            break
            
        time.sleep(2)

if __name__ == "__main__":
    example_url = "https://news.ycombinator.com"
    example_goal = "Get the titles of the top 5 stories on Hacker News."
    
    if len(sys.argv) > 2:
        example_url = sys.argv[1]
        example_goal = sys.argv[2]
        
    test_scrape(example_url, example_goal)
