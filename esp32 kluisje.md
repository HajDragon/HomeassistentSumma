
# Projectrapportage: Monitoringssysteem voor 10 Kluisjes

**Datum:** 24 Maart 2026
**Doel van het project:** Het realiseren van een betrouwbaar elektronisch systeem om de open/dicht-status van 10 kluisjes te monitoren met behulp van één enkele ESP32-microcontroller.

## 1. Hardware Benodigdheden

Voor dit project is gekozen voor een robuuste en onderhoudsvriendelijke setup:

* **Microcontroller:** 1x ESP32 Development Board (bijv. ESP32 NodeMCU of ESP32 WROOM). Gekozen vanwege het ruime aantal GPIO-pinnen en ingebouwde Wi-Fi functionaliteit voor eventuele toekomstige uitbreidingen.
* **Sensoren:** 10x Magneetcontacten (Reed-schakelaars / deurcontacten). Deze bestaan uit een magneet (voor op de deur) en een sensor (voor op het kozijn). Ze zijn slijtvast en betrouwbaar.
* **Bedrading:** Voldoende koperdraad of jumper-kabels om de sensoren met het centrale ESP32-bord te verbinden.
* **Voeding:** 1x 5V Micro-USB of USB-C voeding (afhankelijk van het specifieke ESP32-bord).

## 2. Pin-allocatie (Exacte Board Planning)

De ESP32 heeft specifieke pinnen met speciale functies. Voor dit project vermijden we 'Input-Only' pinnen (omdat die geen interne pull-up weerstanden hebben) en 'Strapping' pinnen (om boot-problemen te voorkomen). De onderstaande pinnen zijn 100% veilig voor gebruik als ingang.

| Kluisje Nummer       | ESP32 GPIO Pin | Type Pin     | Functie in Software |
| -------------------- | -------------- | ------------ | ------------------- |
| **Kluisje 1**  | GPIO 13        | Veilig / I/O | `INPUT_PULLUP`    |
| **Kluisje 2**  | GPIO 14        | Veilig / I/O | `INPUT_PULLUP`    |
| **Kluisje 3**  | GPIO 16        | Veilig / I/O | `INPUT_PULLUP`    |
| **Kluisje 4**  | GPIO 17        | Veilig / I/O | `INPUT_PULLUP`    |
| **Kluisje 5**  | GPIO 18        | Veilig / I/O | `INPUT_PULLUP`    |
| **Kluisje 6**  | GPIO 19        | Veilig / I/O | `INPUT_PULLUP`    |
| **Kluisje 7**  | GPIO 21        | Veilig / I/O | `INPUT_PULLUP`    |
| **Kluisje 8**  | GPIO 22        | Veilig / I/O | `INPUT_PULLUP`    |
| **Kluisje 9**  | GPIO 23        | Veilig / I/O | `INPUT_PULLUP`    |
| **Kluisje 10** | GPIO 25        | Veilig / I/O | `INPUT_PULLUP`    |

## 3. Bedradingsschema (Active-Low Design)

We maken gebruik van de "Active-Low" ontwerpmethode. Dit is de schoonste manier van bedraden, omdat externe weerstanden niet nodig zijn. We maken gebruik van de interne pull-up weerstanden van de ESP32.

**Uitvoeringsplan bedrading:**

1. **Gezamenlijke Aarde (GND):** Verbind van elke magneetschakelaar één draad met elkaar. Sluit deze bundel van 10 draden aan op één **GND-pin** van de ESP32. (Zie Hoofdstuk 6 voor details over hoe je dit met een breadboard doet).
2. **Signaaldraden:** Verbind de tweede (overgebleven) draad van elke magneetschakelaar rechtstreeks met de corresponderende GPIO-pin zoals aangegeven in de tabel.

*Werking:* Bij een gesloten kluisje maakt de schakelaar contact met de aarde (GND), de ESP32 leest `LOW`. Bij een geopend kluisje verbreekt de verbinding met aarde, de interne pull-up weerstand trekt de spanning omhoog naar 3.3V, de ESP32 leest `HIGH`.

## 4. Software Ontwerppatroon

De software is ontworpen met de volgende patronen voor maximale stabiliteit en schaalbaarheid:

* **Object-Georiënteerde Arrays:** De pinnen en statussen worden beheerd in arrays, waardoor de code extreem compact blijft via een simpele `for`-loop.
* **Niet-Blokkerende Debouncing:** Om te voorkomen dat fysieke trillingen in de schakelaar als meerdere open/dicht acties worden geregistreerd, gebruikt de code `millis()` om een signaal pas te accepteren als het 50 milliseconden stabiel is.

## 5. Broncode (C++ / Arduino IDE)

Kopieer deze code naar de Arduino IDE. Selecteer je ESP32 board en upload de code. Open vervolgens de Seriële Monitor (op baudrate 115200) om de statussen van de kluisjes live te volgen.

```
/*
 * Monitoringssysteem voor 10 Kluisjes (ESP32)
 * Ontwerp: Active-Low met Interne Pull-up weerstanden
 */

const int AANTAL_KLUISJES = 10;

// De array met de veilige GPIO pinnen voor de 10 kluisjes
const int kluisPinnen[AANTAL_KLUISJES] = {13, 14, 16, 17, 18, 19, 21, 22, 23, 25};

// Arrays voor het bijhouden van de statussen en debouncing per kluisje
int huidigeStatus[AANTAL_KLUISJES];
int vorigeStatus[AANTAL_KLUISJES];
unsigned long laatsteDebounceTijd[AANTAL_KLUISJES];

// Instelling voor de debouncing (50 ms is standaard voor mechanische schakelaars)
const unsigned long debounceVertraging = 50; 

void setup() {
  // Start seriële communicatie voor output naar de computer
  Serial.begin(115200);
  Serial.println("Kluisjes Monitor Systeem Start...");
  Serial.println("Initialiseren van pinnen...");

  // Stel alle pinnen in via een loop
  for (int i = 0; i < AANTAL_KLUISJES; i++) {
    // Cruciaal: Gebruik INPUT_PULLUP voor het active-low design
    pinMode(kluisPinnen[i], INPUT_PULLUP);
  
    // Beginwaardes instellen (HIGH betekent dat de verbinding open is)
    huidigeStatus[i] = HIGH; 
    vorigeStatus[i] = HIGH;
    laatsteDebounceTijd[i] = 0;
  }
  
  Serial.println("Systeem is gereed.");
}

void loop() {
  // Loop continu door alle 10 kluisjes
  for (int i = 0; i < AANTAL_KLUISJES; i++) {
    // Lees de huidige fysieke waarde van de pin
    int leesWaarde = digitalRead(kluisPinnen[i]);

    // Controleer of de status is veranderd (kan ruis zijn of een echte actie)
    if (leesWaarde != vorigeStatus[i]) {
      // Reset de debounce timer voor dit specifieke kluisje
      laatsteDebounceTijd[i] = millis();
    }

    // Controleer of de status langer stabiel is dan de debounce vertraging
    if ((millis() - laatsteDebounceTijd[i]) > debounceVertraging) {
    
      // Als de stabiele status anders is dan de laatst bekende status
      if (leesWaarde != huidigeStatus[i]) {
        huidigeStatus[i] = leesWaarde; // Update de status

        // Print de nieuwe status naar de Seriële Monitor
        Serial.print("Kluisje ");
        Serial.print(i + 1); // +1 zodat we tellen vanaf 1 i.p.v. 0
      
        // LOW = Verbonden met GND (Magneet bij sensor = Dicht)
        // HIGH = Verbinding verbroken (Magneet weg = Open)
        if (huidigeStatus[i] == LOW) {
          Serial.println(" is GESLOTEN.");
        } else {
          Serial.println(" is OPEN.");
        }
      }
    }
  
    // Sla de gelezen waarde op voor de volgende iteratie van de loop
    vorigeStatus[i] = leesWaarde;
  }
}
```

## 6. Bijlage: Hoe gebruik je een Breadboard?

Omdat je 10 kluisjes hebt, moet je van alle 10 de sensoren één draad verbinden met de "Aarde" (Ground / GND). De ESP32 microcontroller heeft maar een paar piepkleine GND-pinnetjes. Het is fysiek onmogelijk om 10 draden in één zo'n klein gaatje te proppen.

Daarvoor gebruiken we een  **Breadboard** .

### Wat is een Breadboard?

Een breadboard is een plastic bordje met heel veel kleine gaatjes erin. Het is ontworpen om elektronica-onderdelen en draden met elkaar te verbinden  **zonder dat je hoeft te solderen** . Je steekt de draadjes er simpelweg in. Onder het plastic zitten ijzeren klemmetjes die bepaalde gaatjes met elkaar verbinden.

Als je snapt hoe die gaatjes met elkaar verbonden zijn, is het heel makkelijk:

### Hoe werkt het van binnen?

Op een standaard breadboard zie je twee soorten rijen met gaatjes:

1. **De lange lijnen aan de zijkant (Stroomrails):**
   Aan de zijkanten zie je lange rijen met een rode lijn (Plus / +) en een blauwe of zwarte lijn (Min / -).
   * **Het geheim:** Alle gaatjes naast een blauwe lijn zijn *onderhuids allemaal met elkaar verbonden* tot één lange metalen strip. Als je in het bovenste gaatje stroom stopt, staat er op het onderste gaatje (en alle gaatjes daartussen) ook stroom.
2. **De korte rijtjes in het midden:**
   In het midden zie je rijtjes van 5 gaatjes (vaak genummerd als 1, 2, 3... en letters A t/m E). Deze zijn *horizontaal* met elkaar verbonden. (Deze heb je voor dit specifieke project bijna niet nodig).

### Stappenplan voor dit kluisjes-project:

We gaan de lange **blauwe min-lijn (-)** van het breadboard gebruiken om al onze 10 draden netjes te bundelen.

Volg deze simpele stappen:

* **Stap 1: Verbind de ESP32 met het breadboard.** Neem één kort kabeltje. Steek de ene kant in een  **GND** -pin van je ESP32. Steek de andere kant in een willekeurig gaatje van de lange **blauwe lijn (-)** op je breadboard.
  *(Gefeliciteerd! Nu is die hele lange blauwe rij op je breadboard veranderd in één gigantische GND-pin).*
* **Stap 2: Verbind de kluisjes.**
  Neem nu het magneetcontact van Kluisje 1. Dit contact heeft twee draden. Kies er één uit (maakt niet uit welke). Steek deze draad in een leeg gaatje op diezelfde lange **blauwe lijn (-)** van het breadboard.
* **Stap 3: Herhalen.**
  Doe precies hetzelfde voor de andere 9 kluisjes. Pak van elk kluisje één draad en prik deze in een leeg gaatje op de  **blauwe lijn (-)** .
* **Stap 4: De signaaldraden (de andere helft).**
  Nu houd je van elk kluisje nog één draad over. Deze gaan *niet* in de blauwe lijn. Deze prik je rechtstreeks in de specifieke pinnen op de ESP32 (Pin 13, Pin 14, Pin 16, etc.) zoals beschreven in Hoofdstuk 2 van dit rapport.

**Waarom is dit briljant?**
Omdat alle 10 de kluisjes nu via de blauwe lijn op het breadboard verbonden zijn met dat ene korte kabeltje dat naar de ESP32 gaat. Je hebt zojuist 10 draden samengevoegd tot 1 draad, zonder gereedschap, zonder tape en zonder solderen!
