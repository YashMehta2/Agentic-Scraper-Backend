import requests, json, time, sys

job_id = sys.argv[1] if len(sys.argv) > 1 else "5a9ce40f-b283-4be1-9a1a-74c6be00650e"

for i in range(15):
    r = requests.get(f"http://localhost:8000/status/{job_id}").json()
    status = r["status"]
    print(f"[{i*5}s] Status: {status}")
    if status in ("COMPLETED", "FAILED"):
        print(json.dumps(r, indent=2))
        break
    time.sleep(5)
else:
    print("Timed out waiting for job.")
