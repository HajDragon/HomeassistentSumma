# ESP32-C6 Spanningssensor (ESPHome & Arduino C naar Home Assistant)

Dit document beschrijft de code en installatie om een Seeed Studio XIAO ESP32-C6 te programmeren voor het detecteren van spanning op pin D6 (GPIO 11) en de status hiervan automatisch te rapporteren aan Home Assistant. We behandelen zowel de aanbevolen ESPHome YAML-methode als de handmatige Arduino C-methode.

## Benodigdheden

* **Bord:** Seeed Studio XIAO ESP32-C6
* **Voor ESPHome (Methode 1):** ESPHome add-on geïnstalleerd in Home Assistant.
* **Voor Arduino C (Methode 2):** Arduino IDE met de `esp32` board manager geïnstalleerd, de `PubSubClient` bibliotheek, en de Mosquitto MQTT broker add-on draaiend in Home Assistant.

## Hardware Aansluiting

* **Sensor Signaal:** Sluit de signaaldraad aan op fysieke pin **D6** (wat intern GPIO 11 is).
* **Sensor Aarde (Ground):** Sluit de aardedraad aan op de fysieke pin  **GND** .
* **Spanningslimiet:** Zorg ervoor dat de sensor maximaal **3,3V** afgeeft! Een hogere spanning zal het bord beschadigen.

## Methode 1: De ESPHome YAML Code (Aanbevolen & Eenvoudig)

Deze methode is het makkelijkst en vereist geen aparte netwerkcode. Plak dit eenvoudigweg onderaan het configuratiebestand van je apparaat in het ESPHome-dashboard.

```
binary_sensor:
  - platform: gpio
    pin: 
      number: 11
      mode: INPUT_PULLDOWN
    name: "Mijn Sensor Status"
```

## Methode 2: De Arduino C Code (Geavanceerd via MQTT)

Als je liever ruwe C++ code schrijft, gebruikt dit script MQTT Auto-Discovery zodat de sensor alsnog automatisch in Home Assistant verschijnt.

#include <WiFi.h>
#include <PubSubClient.h>

// ==========================================
// 1. UPDATE JE NETWERK & MQTT INSTELLINGEN
// ==========================================
const char* ssid = "JOUW_WIFI_SSID";
const char* password = "JOUW_WIFI_WACHTWOORD";

const char* mqtt_server = "192.168.1.X"; // Het IP-adres van je Home Assistant
const int mqtt_port = 1883;
const char* mqtt_user = "JOUW_MQTT_GEBRUIKERSNAAM";
const char* mqtt_password = "JOUW_MQTT_WACHTWOORD";

// ==========================================
// 2. PIN & HARDWARE INSTELLINGEN
// ==========================================
const int sensorPin = 11; // GPIO 11 komt overeen met D6 op de XIAO ESP32-C6
int lastSensorState = -1;

// ==========================================
// 3. MQTT TOPICS
// ==========================================
const char* state_topic = "xiao_c6/sensor/state";
const char* config_topic = "homeassistant/binary_sensor/xiao_c6_sensor/config";

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Verbinden met ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi verbonden.");
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Bezig met MQTT verbinding maken...");

    // Probeer te verbinden met een unieke client ID
    if (client.connect("XiaoC6Client", mqtt_user, mqtt_password)) {
      Serial.println("verbonden");

    // --- HOME ASSISTANT AUTO-DISCOVERY PAYLOAD ---
      String discoveryPayload = "{\"name\": \"Mijn Sensor Status\", \"state_topic\": \"xiao_c6/sensor/state\", \"unique_id\": \"xiao_c6_pin11\", \"device\": {\"identifiers\": [\"xiao_c6\"], \"name\": \"XIAO ESP32-C6\"}}";

    client.publish(config_topic, discoveryPayload.c_str(), true);

    } else {
      Serial.print("mislukt, rc=");
      Serial.print(client.state());
      Serial.println(" probeer het over 5 seconden opnieuw");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(sensorPin, INPUT_PULLDOWN);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  int currentSensorState = digitalRead(sensorPin);
  if (currentSensorState != lastSensorState) {
    if (currentSensorState == HIGH) {
      Serial.println("Spanning gedetecteerd - Verstuur ON");
      client.publish(state_topic, "ON");
    } else {
      Serial.println("Geen spanning - Verstuur OFF");
      client.publish(state_topic, "OFF");
    }
    lastSensorState = currentSensorState;
  }
  delay(50);
}
