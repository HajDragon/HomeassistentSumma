import requests
import json
import sys

def trigger_camera_event():
    """
    Sends a POST request to a Home Assistant webhook to trigger a camera event.
    """
    # The target URL for the Home Assistant webhook
    webhook_url = "http://homeassistant.local:8123/api/webhook/-p495cjMzRhBPWIZ6bBKIgxrA"
    
    # JSON payload to send with the request
    # This data can be used in Home Assistant automations
    payload = {
        "action": "capture", 
        "source": "python_script"
    }
    
    # Headers to specify that we are sending JSON data
    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Sending a POST request to the webhook URL
        # json=payload auto-adds the Content-Type header, but adding explicitly for clarity
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
        
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print(f"Success! Webhook triggered. Status Code: {response.status_code}")
        else:
            print(f"Failed to trigger webhook. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Home Assistant. Check the URL and ensure Home Assistant is running.")
    except requests.exceptions.Timeout:
        print("Error: The request timed out.")
    except requests.exceptions.RequestException as e:
        # Catch-all for other request-related errors
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    trigger_camera_event()
