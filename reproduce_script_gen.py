import requests
import json
import time

def reproduce():
    print("Sending request to /api/scripts/generate...")
    payload = {
        "story_title": "Test Story",
        "story_premise": "A test story about debugging.",
        "story_genre": "News",
        "story_audience": "General",
        "duration": "30s"
    }
    
    start_time = time.time()
    try:
        response = requests.post(
            "http://localhost:8001/api/scripts/generate",
            json=payload,
            timeout=300
        )
        end_time = time.time()
        print(f"Response received in {end_time - start_time:.2f} seconds.")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Success!")
            # print(json.dumps(response.json(), indent=2))
        else:
            print("Failed!")
            print(response.text)
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    reproduce()
