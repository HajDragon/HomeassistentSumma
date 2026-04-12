# Beheerdershandleiding: Cardiac Monitoring Dashboard

## Doel

Deze handleiding is bedoeld voor mensen die de slimme kamer gebruiken en helpen beheren, maar geen technische ervaring hebben. De uitleg is kort, eenvoudig en gericht op wat u in de praktijk moet doen in Home Assistant.

## Het dashboard gebruiken

Op het dashboard ziet u informatie over de kamer, camera’s, sensoren en metingen. Alles is gemaakt om snel te kunnen zien wat er aan de hand is.

Belangrijk om te onthouden:

- Gebruik het dashboard rustig en klik alleen op wat u nodig heeft.
- Als een scherm er vreemd uitziet, vernieuw dan eerst de pagina.
- Wacht na een meting even totdat de gegevens zichtbaar worden.
- Klik niet op het potloodje om het dashboard te bewerken, tenzij u echt iets wilt aanpassen.
- Zorg dat de tablet of computer verbonden is met het juiste wifi-netwerk.
- Laat het dashboard open staan tijdens de les, zodat metingen goed zichtbaar blijven.

## Wat studenten moeten weten

Deze punten helpen studenten en begeleiders om rustig met het systeem te werken:

- Een camera of sensor kan even wachten op nieuwe informatie.
- Als een waarde nog niet zichtbaar is, hoeft dat niet meteen een fout te zijn.
- Na een meting kan het even duren voordat de cijfers op het scherm verschijnen.
- Gebruik de knoppen op het scherm alleen als u zeker weet wat ze doen.
- Meld problemen liever meteen, zodat iemand kan kijken of alles nog goed werkt.

## Camera geeft geen beeld

Als een camera geen beeld laat zien, probeer dan eerst een harde verversing van de pagina:

1. Druk op Ctrl + F5.
2. Kijk daarna opnieuw of het camerabeeld terug is.

Als er nog steeds geen beeld is, volg dan deze stappen:

1. Ga naar Instellingen.
2. Kies Apparaten en diensten.
3. Open Integraties.
4. Kies Reolink.
5. Zoek de camera Backside of front door.
6. Klik rechts op de drie puntjes bij die camera.
7. Kies Reload.

Daarna wordt de camera-informatie opnieuw geladen.

## Sensor zegt "Unavailable" of "Niet beschikbaar"

Als een sensor de tekst Unavailable of Niet beschikbaar toont, betekent dit niet meteen dat de sensor kapot is.

Dit kan twee dingen betekenen:

- De sensor heeft nog geen nieuwe meting ontvangen.
- We hebben op dit moment geen apparaat dat precies die waarde doorgeeft, bijvoorbeeld huidtemperatuur.

Zodra er een meting wordt gedaan, verandert de sensor meestal vanzelf van Niet beschikbaar naar een getal.

## Withings-metingen synchroniseren

Wanneer studenten een meting doen in de kamer, moet de gegevensstroom soms handmatig worden ververst zodat de waarden op het dashboard komen.

Doe dan het volgende:

1. Ga naar Instellingen.
2. Kies Apparaten en diensten.
3. Open Integraties.
4. Kies Withings.
5. Klik rechts op de drie puntjes bij de integratie.
6. Kies Reload.

Daarna worden de nieuwste metingen opnieuw ingeladen op het dashboard.

## Belangrijke aandachtspunten

Deze punten helpen om problemen te voorkomen:

- Zet camera’s, sensoren en schermen niet zomaar uit of los, want dan kan informatie verdwijnen.
- Controleer na een meting altijd even of de nieuwe waarde zichtbaar is.
- Gebruik Reload bij Reolink of Withings als gegevens niet binnenkomen.
- Vernieuw de pagina eerst als iets plotseling leeg lijkt of niet goed wordt weergegeven.
- Gebruik geen instellingen die u niet nodig heeft.

## Veelgestelde vragen

### Waarom zie ik nog geen meting?

Soms is de meting nog niet doorgestuurd. Wacht even en vernieuw daarna de pagina. Bij Withings kan Reload helpen.

### Waarom staat er Niet beschikbaar?

Dat betekent meestal dat Home Assistant nog geen waarde heeft ontvangen, of dat er voor dat onderdeel geen apparaat is. Het is dus niet altijd een fout.

### Waarom doet de camera het soms wel en soms niet?

Soms moet het beeld even opnieuw worden geladen. Probeer eerst Ctrl + F5. Helpt dat niet, dan kan Reolink opnieuw worden ingeladen met Reload.

### Mag ik op het potloodje klikken?

Alleen als u het dashboard echt wilt aanpassen. Voor normaal gebruik is dat niet nodig.

### Wat als de pagina raar blijft doen?

Probeer eerst te vernieuwen. Als dat niet helpt, controleer of de tablet of computer op het juiste netwerk zit en vraag daarna hulp.

## Algemene problemen en oplossingen

### Het dashboard laadt niet goed

1. Vernieuw de pagina.
2. Controleer de wifi-verbinding.
3. Sluit de browser en open het dashboard opnieuw.

### Een custom kaart laat niets zien

Soms moet de pagina opnieuw worden geladen voordat een speciale kaart goed werkt.

1. Vernieuw de pagina.
2. Kijk of de kaart terugkomt.
3. Meld het als de kaart daarna nog steeds leeg blijft.

### Waarden veranderen niet na een meting

1. Wacht een kort moment.
2. Vernieuw de pagina.
3. Gebruik Reload bij Withings.

### Camera of sensor blijft op hetzelfde scherm staan

1. Vernieuw de pagina.
2. Controleer of het juiste scherm openstaat.
3. Gebruik Reload bij de juiste integratie.

## Samenvatting voor dagelijks gebruik

Als iets niet goed lijkt te werken, onthoud dan deze volgorde:

1. Vernieuw de pagina.
2. Controleer of u op het juiste scherm en netwerk zit.
3. Gebruik Reload bij Reolink of Withings als de gegevens niet binnenkomen.
4. Kijk of de sensor na een meting vanzelf bijwerkt.

Met deze stappen kunt u de meeste problemen snel oplossen zonder technische kennis.
