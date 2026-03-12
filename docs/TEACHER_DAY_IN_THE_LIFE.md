# Teacher's Guide: A Day in the Life — Smart Room Simulation Dashboard

> **Who is this guide for?**
> This guide is written for classroom teachers who use the Smart Room Simulation Dashboard during lessons. No technical knowledge is needed. If anything stops working, a note at the end of each section tells you exactly who to call.

---

## Before You Begin: What You See on Screen

When you open the simulation dashboard, you will see:

- Two side-by-side **control panels** at the top of the screen:
- - **Left panel ("Huidige Meetwaarden")** — displays the *current* body scan readings for the patient (e.g., Mevrouw Goedheid). Think of this as the read-only display you would show to students.
  - **Right panel ("Simulatie Invoer")** — contains the orange sliders you use to *set* the values for each measurement point. This is your teacher control panel.
- A **"Sync meetwaarden → Run"** button in the right panel. This button copies real device readings into the simulation so they become the new starting point.
- A **data table** below the panels showing all recorded measurements across each time period.
- **Line graphs** at the bottom tracking trends over the 6-month simulation.

---

## Part 1: Initial Check — What to Do Before the Lesson Starts

Allow **5 minutes** before students arrive to run through these checks.

### Step 1 — Open the Dashboard

Navigate to the **Simulatie** tab in the Home Assistant app on the classroom tablet or browser. You should land directly on the *Mevrouw Goedheid* simulation view.

### Step 2 — Confirm the Data Source is Set to "Simulatie"

Look at the top of the left panel for the **Databron** (Data Source) dropdown.

- It should read **"Simulatie"** for a classroom demo.
- If it shows **"Live Data (Echte Weegschaal)"**, tap it and switch it back to **Simulatie**. Live Data is only used when a real body-scan scale is physically connected.

### Step 3 — Check the Simulation Phase

In the top-right area, confirm which **Meting** button is highlighted (Meting 1, 2, 3, or 4).

- For a fresh start, press the red **Reset Simulatie** button (you will be asked to confirm).
- The display will reset to zeroes — this is normal and expected.

### Step 4 — Verify the Orange Sliders Are Responsive

In the right panel, gently slide the **Lichaamslengte** (body height) slider slightly up and back. The corresponding value in the left panel should update within one second. If it does not update, notify your system administrator before the lesson begins.

---

## Part 2: Core Task Workflow — Running a 6-Month Body Scan Simulation

This is the most common task you will perform. The simulation models a patient (Mevrouw Goedheid) whose body composition is measured four times over six months. Each step below takes roughly **2–3 minutes** of lesson time.

---

### Step 1 — Start at Meting 1 (the Baseline)

Tap the **"Meting 1"** button (marked with a circled number 1). This sets the room to the first measurement point: **1 January 2026 — the patient's starting condition.**

> What happens: The sliders in the right panel jump to the baseline values (e.g., weight 70.0 kg, BMI 24.8). The left panel immediately shows these same values as the "current reading".

**Ask students:** *"What do these numbers tell us about Mevrouw Goedheid's health at the start?"*

---

### Step 2 — Progress to Meting 2 (Two Months Later)

Tap **"Meting 2"**. The date advances to **1 March 2026** and all values update to reflect two months of change.

> What happens: Weight rises slightly (72.0 kg), BMI increases (25.5), muscle mass holds nearly steady (29.3 kg), and fat mass grows (25.5 kg).

**Ask students:** *"Which number changed the most? What lifestyle factor might explain that?"*

---

### Step 3 — Advance to Meting 3 and Meting 4

Tap **"Meting 3"** (May 2026) and then **"Meting 4"** (July 2026) in sequence. Pause after each one to let students compare the values.

> Meting 4 values: Weight 77.0 kg (+7 kg overall) · BMI 27.3 · Muscle mass 28.8 kg (−0.7 kg) · Fat mass 28.5 kg (+4.5 kg).

The **trend arrows** in the reference table at the bottom confirm the overall direction:

- Weight ↑ · Fat mass ↑ · Muscle mass ↓ · BMI ↑

---

### Step 4 — Adjust a Value to Test a "What If" Scenario (Optional)

You can change any single measurement to explore a hypothetical. For example: *"What if Mevrouw Goedheid had exercised more and gained muscle instead of fat?"*

1. Make sure you are on **Meting 4** (or whichever phase you want to modify).
2. In the **right panel**, drag the orange **Spiermassa** (muscle mass) slider upward to a new value — for example, 31.0 kg.
3. The left panel updates in real time. The graph at the bottom will show the adjusted data point.

> **Important:** This change is temporary. Pressing any Meting button or the Reset button will restore the original scenario values.

---

### Step 5 — Sync Real-World Data (Only if a Live Scale Is Connected)

If a physical body-scan scale (Withings) is present in the room:

1. Have the student or volunteer stand on the scale and allow it to complete the measurement.
2. Switch the **Databron** dropdown to **"Live Data (Echte Weegschaal)"**.
3. Tap the **"Sync meetwaarden → Run"** button visible in the right panel. This copies the live reading into the simulation so it can be compared with the scenario data.
4. Switch **Databron** back to **"Simulatie"** when done to prevent the live feed from overwriting your lesson data.

---

## Part 3: Reading the Charts and Status Indicators

### The Data Table (Middle of the Screen)

| Column                    | What it Means                                          |
| ------------------------- | ------------------------------------------------------ |
| **Datum**           | The calendar date of that measurement point            |
| **Gewicht (kg)**    | Total body weight                                      |
| **Spiermassa (kg)** | Lean muscle mass — higher is generally healthier      |
| **Vetmassa (kg)**   | Body fat mass — used alongside BMI for a full picture |
| **BMI (kg/m²)**    | Body Mass Index — a ratio of weight to height         |

A **pulsing amber row** in the table means a slider has been moved but the value has not yet been saved (the system saves automatically after about 1 second). Wait for the amber highlight to disappear before advancing to the next Meting.

### The Line Graphs (Bottom of the Screen)

There are four separate graphs — one each for Weight, BMI, Muscle Mass, and Fat Mass. Each graph shows a line connecting all four measurement points (Meting 1 through 4).

| Graph Shape         | What to Tell Students                                   |
| ------------------- | ------------------------------------------------------- |
| Line rising steeply | The metric increased significantly over six months      |
| Line rising gently  | Gradual change — likely within normal variation        |
| Line falling        | Improvement (for fat mass) or concern (for muscle mass) |
| Flat line           | The value was consistent across all four periods        |

**Teaching tip:** Ask students to predict the next point on the graph before you advance to the next Meting. This builds analytical thinking before the data is revealed.

---

## Part 4: Troubleshooting — When Something Looks Wrong

### The Left Panel Shows "Unknown" or Dashes

**Cause:** The simulation is in "Reset / Startklaar" state — no measurement has been selected yet.
**Fix:** Tap **Meting 1** to load the baseline values.

### A Slider in the Right Panel Is Greyed Out

**Cause:** The Databron is set to "Live Data (Echte Weegschaal)". In this mode, sliders are disabled because the system reads directly from the scale.
**Fix:** Switch the **Databron** dropdown back to **"Simulatie"**.

### The "Sync meetwaarden → Run" Button Shows a Red Indicator

**Cause:** The sync script could not reach the live scale. The scale may be off, out of Bluetooth range, or not yet connected.
**Fix:** Do not press Run repeatedly. Switch Databron back to "Simulatie" and continue the lesson using the preset scenario values. Ask your system administrator to check the scale connection after class.

### The Graphs Are Empty or Not Updating

**Cause:** The statistics graphs collect data over time. If the simulation was just reset, or if this is the first time Meting values have been entered, the graph needs at least two data points before it draws a line.
**Fix:** Advance through at least two Meting buttons (e.g., Meting 1, then Meting 2). The line should appear after the second point is recorded.

### The Dashboard Stops Responding Entirely

**Fix:** Refresh the browser page (press F5 on a keyboard, or pull down on a tablet). If the problem continues, contact your system administrator. Do not try to change any settings in the Home Assistant menu — this is outside the scope of the classroom application and may affect other lessons.

---

## Quick Reference Card

| Task                  | Where to Find It              | What to Press                                           |
| --------------------- | ----------------------------- | ------------------------------------------------------- |
| Start fresh           | Top-right area                | Red**Reset Simulatie** button, then confirm       |
| Load baseline data    | Top-right grid                | **Meting 1** button                               |
| Advance the timeline  | Top-right grid                | **Meting 2**, **3**, or **4** buttons |
| Adjust a single value | Right panel — orange sliders | Drag the slider left or right                           |
| Sync real scale data  | Right panel — bottom row     | **Sync meetwaarden → Run** button                |
| Switch data source    | Left panel — Databron row    | Tap the dropdown and select option                      |

---

## Who to Contact

| Situation                          | Contact                                        |
| ---------------------------------- | ---------------------------------------------- |
| Dashboard won't load               | System Administrator                           |
| Scale not connecting               | System Administrator                           |
| Wrong patient scenario loaded      | System Administrator                           |
| Questions about the lesson content | Your department head or curriculum coordinator |

---

*This guide covers the Mevrouw Goedheid — Body Scan Simulation. Document version: March 2026.*
