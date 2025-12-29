# Ultrasonic-Distance-Logger

An Arduino Ultrasonic distance logger (HC-SR04) with statistical based filtering, live analysis and CSV export.

## Installation

Install the dependencies with the following command:

```
pip install -r requirements.txt
```

This project measures distance using an **Arduino Nano with a HC-SR04 ultrasonic sensor**, and processes the data through a Python filtering and logging pipeline. The goal is to take raw, unfiltered data, clean and filter them, then produce **accurate measurements** for analysis. The objective is to receive raw undisturbed data, clean them, scale and filter in order to obtain accurate measures for analysis purposes. The ultrasonic sensor can be very noisy because jumps / impossible / noise distance spikes, this system performs **statistical filtering** to discard out-of-value (range) values. Instead of trusting a single reading, this program collects multiple readings into a batch, filters them, then outputs an accurate measurement. All can be done **live** while the Arduino is connected via usb.

## FEATURES
- Reads the **raw echo (microseconds)** of the sound waves streamed over **serial** from the Arduino. 
- Python then converts time of flight values into distance (cm) using a **temperature-based speed of sound**.
- Batches N sensor samples to reduce single-reading noise
- Uses **statistical filtering**
  - Median-centered filtering
  - Script reads the batch of N values, uses **percentile/IQR filter** around median to remove spikes / impossible jumps
  - Returns the **average** as the final distance.
- **Live anaylysis** of distances, visually differentiating raw vs filtered
- All clean logs, stats, and raw data results are imported to a **CSV file** for human analysis if needed (e.g., calibration, accuracy tests, graphing, research).

## HARDWARE
- Arduino Nano
- HC-SR04 Ultrasonic Sensor
- Jumper wires / breadboard
- USB cable to PC

## USAGE
The code is provided for the Arduino Nano and the ultrasonic sensor, it is recommended to use the sketch code for predictable behaviour.
- Upload the sketch to your Nano
- Edit `config.ini` to your preference (COM port, runtime duration, sample batch size (Recommended 10), temperature (°C), min/max distance thresholds)
- Run `python main.py`, see live readings from Arduino (raw vs filtered)
- Generated CSV file (raw sensor values, filtered data, spread, quartiles, final computed distances, timestamps, median, boundaries)
