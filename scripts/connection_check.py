import os
import sys
import requests
import json
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

HA_BASE_URL = os.getenv("HA_BASE_URL", "http://homeassistant.local:8123").rstrip("/")
HA_TOKEN    = os.getenv("HA_TOKEN")
if not HA_TOKEN:
    sys.exit("Error: HA_TOKEN not set — copy .env.example to .env and fill in your token.")


def check_homeassistant_heartbeat():
    """Check Home Assistant heartbeat and system status"""

    base_url = HA_BASE_URL
    token    = HA_TOKEN
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("=" * 50)
    print("HOME ASSISTANT HEARTBEAT CHECK")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Check API status
        print("1. Testing API connection...")
        response = requests.get(f"{base_url}/api/", headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"   ✓ API Status: {response.json().get('message')}")
        else:
            print(f"   ✗ API Error: {response.status_code}")
            return
        
        # Get system config
        print("\n2. Fetching system information...")
        config_response = requests.get(f"{base_url}/api/config", headers=headers, timeout=5)
        if config_response.status_code == 200:
            config = config_response.json()
            print(f"   ✓ Version: {config.get('version', 'Unknown')}")
            print(f"   ✓ Location: {config.get('location_name', 'Unknown')}")
            print(f"   ✓ Time Zone: {config.get('time_zone', 'Unknown')}")
            print(f"   ✓ Unit System: {config.get('unit_system', {}).get('length', 'Unknown')}")
        
        # Get system states count
        print("\n3. Checking entities...")
        states_response = requests.get(f"{base_url}/api/states", headers=headers, timeout=5)
        if states_response.status_code == 200:
            states = states_response.json()
            print(f"   ✓ Total entities: {len(states)}")
            
            # Count by domain
            domains = {}
            for state in states:
                domain = state['entity_id'].split('.')[0]
                domains[domain] = domains.get(domain, 0) + 1
            
            print(f"   ✓ Cameras: {domains.get('camera', 0)}")
            print(f"   ✓ Sensors: {domains.get('sensor', 0)}")
            print(f"   ✓ Lights: {domains.get('light', 0)}")
        
        print("\n" + "=" * 50)
        print("✓ HOME ASSISTANT IS HEALTHY")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to Home Assistant")
        print("  Check if Home Assistant is running at homeassistant.local:8123")
    except requests.exceptions.Timeout:
        print("\n✗ ERROR: Connection timeout")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")

if __name__ == "__main__":
    check_homeassistant_heartbeat()
