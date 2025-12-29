# ultrasonic-distance-logger
Arduino ultrasonic distance logger with Python-based filtering, calibration, and CSV export.
Install all necessary dependencies using the following command in console or powershell:

pip install -r requirements.txt

This project measures distance using an Arduino Nano + HC-SR04 ultrasonic sensor, and processes the data through a Python filtering and logging pipeline.

Reads the raw echo (microseconds) of the sound waves sent streamed over serial from the Arduino. Python then converts these values into distance (cm) using a temperature-based speed of sound. The ultrasonic sensor can be quite inaccurate due to jumps / impossible / noise spikes in distances, this system applies statistical filtering to rejects out-of-range values. The script reads a batch of N values sent from the sensor, then uses percentile/IQR filter around median to remove spikes, and returns the average as the final distance. When the function ends after a certain amount of time, all clean logs, stats, and raw data results are imported to a CSV file for human analysis if needed (e.g., calibration, accuracy tests, graphing, research).
