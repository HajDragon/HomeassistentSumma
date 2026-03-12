import sys

import requests
import json
from collections import defaultdict
from dotenv import load_dotenv
import os

def list_homeassistant_devices():
    """Fetch and display all Home Assistant devices and entities grouped by type"""
        
    load_dotenv()

    _HA_BASE_URL = os.getenv("HA_BASE_URL", "http://homeassistant.local:8123").rstrip("/")
    TOKEN        = os.getenv("HA_TOKEN")
    if not TOKEN:
        sys.exit("Error: HA_TOKEN not set — copy .env.example to .env and fill in your token.")

    WS_URL = _HA_BASE_URL.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket"

    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Fetch all states/entities
        response = requests.get(f"{_HA_BASE_URL}/api/states", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Error: Failed to fetch entities (Status {response.status_code})")
            return
        
        entities = response.json()
        
        # Group entities by domain
        grouped = defaultdict(list)
        for entity in entities:
            entity_id = entity.get('entity_id', '')
            domain = entity_id.split('.')[0] if '.' in entity_id else 'unknown'
            
            # Get friendly name or use entity_id
            friendly_name = entity.get('attributes', {}).get('friendly_name', entity_id)
            state = entity.get('state', 'unknown')
            
            grouped[domain].append({
                'entity_id': entity_id,
                'friendly_name': friendly_name,
                'state': state
            })
        
        # Domain name mapping for better display
        domain_names = {
            'light': '💡 Lights',
            'switch': '🔌 Switches',
            'sensor': '📊 Sensors',
            'binary_sensor': '🔘 Binary Sensors',
            'camera': '📷 Cameras',
            'media_player': '🎵 Media Players',
            'climate': '🌡️ Climate',
            'cover': '🚪 Covers',
            'lock': '🔒 Locks',
            'fan': '💨 Fans',
            'vacuum': '🤖 Vacuums',
            'device_tracker': '📍 Device Trackers',
            'person': '👤 Persons',
            'zone': '📍 Zones',
            'automation': '⚙️ Automations',
            'script': '📜 Scripts',
            'scene': '🎬 Scenes',
            'input_boolean': '🔘 Input Booleans',
            'input_number': '🔢 Input Numbers',
            'input_select': '📋 Input Selects',
            'input_text': '✏️ Input Text',
            'input_datetime': '📅 Input Datetime',
            'timer': '⏲️ Timers',
            'counter': '🔢 Counters',
            'weather': '🌤️ Weather',
            'sun': '☀️ Sun',
            'group': '📦 Groups',
            'alert': '🚨 Alerts',
            'remote': '📱 Remotes',
            'update': '🔄 Updates',
            'button': '🔘 Buttons',
        }
        
        # Print results
        print("=" * 70)
        print("HOME ASSISTANT DEVICES & ENTITIES")
        print("=" * 70)
        print(f"\nTotal Entities: {len(entities)}")
        print(f"Total Types: {len(grouped)}\n")
        
        # Sort domains by entity count (descending)
        sorted_domains = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)
        
        for domain, items in sorted_domains:
            display_name = domain_names.get(domain, f'📌 {domain.replace("_", " ").title()}')
            print(f"\n{display_name} ({len(items)})")
            print("-" * 70)
            
            # Sort items by friendly name
            items.sort(key=lambda x: x['friendly_name'].lower())
            
            for item in items:
                # Format state for display
                state = item['state']
                if state in ['on', 'off', 'home', 'not_home']:
                    state_display = f"[{state.upper()}]"
                elif state == 'unavailable':
                    state_display = "[UNAVAILABLE]"
                elif len(state) > 30:
                    state_display = f"[{state[:27]}...]"
                else:
                    state_display = f"[{state}]"
                
                print(f"  • {item['friendly_name']}")
                print(f"    └─ ID: {item['entity_id']} {state_display}")
        
        print("\n" + "=" * 70)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Home Assistant")
    except requests.exceptions.Timeout:
        print("Error: Connection timeout")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_homeassistant_devices()
