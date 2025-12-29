from configparser import ConfigParser
import serial, time, csv, os

file = 'config.ini'
config = ConfigParser()
config.read(file)
MIN_DISTANCE_CM = int(config['config']['MIN_DISTANCE_CM'])
MAX_DISTANCE_CM = int(config['config']['MAX_DISTANCE_CM'])
BOUNDARY_MULTIPLIER = float(config['config']['BOUNDARY_MULTIPLIER'])
CSV_FILE_NAME = str("log_at_" + time.strftime('%H_%M_%S'))


def sound_of_speed(temperature):
    #Return speed of sound in cm/µs at given temperature (°C)
    # Parameters
    # Temperature:  Int
    #               Temperature of the current room (Default is 20)
    cm = 100
    microseconds = 1000000  #1000000 microseconds in a second
    cmPerMicrosecond = cm / microseconds
    return float((331.4 + 0.606 * temperature) * cmPerMicrosecond) 

def serialize_arduino(comport, baudrate, seconds, sample, temperature):
    '''
    This function reads the *DURATION* in microseconds from the arduino 
    sensor (tested on hrs04 ultrasonic sensor) and packs a set number of 
    readings (sample) to be sent for analysis. The goal is to get rid of
    garage readings / errors. 
    (Note that the sensor works by playing audio then waits for it to bounce back and then
    returns duration in microseconds)

    Parameters (All adjustable in config.ini):
    comport:     String
                Comport of which the arduino is connected to (Default is 'COM5')
                
    baudrate:    Int
                Which baudrate to read data from (Default is 9600)

    seconds:     Int
                How long the function should analyze the readings (Default is 30)

    sample:      Int
                How many readings should be packed then sent for analysis (Default is 10)

    temperature: Int
                The temperature of the room currently (Default is 20)
    Returns: None
    '''
    count = 0 #We need to count how many readings we got in total, including errors
    error = 0 #We need to count the errors for feedback
    sound = sound_of_speed(temperature)
    arduino_data = [{}]
    sampleArray = [] #Creating the array we will use for the sample
    try:
        ser = serial.Serial(comport, baudrate, timeout=0.1) 
    except serial.SerialException:
        print("COULD NOT OPEN PORT / DEVICE ISNT CONNECTED / PERMISSION DENIED / OPENING AND CLOSING PORTS TOO FAST")
        return
    

    
    loop_end = time.time() + seconds #This times the function and ends it after the set certain amount of time has passed
    while time.time() < loop_end:
        try:
            data = ser.readline().decode().strip() #Initializing each duration Arduino will send over
        except UnicodeDecodeError:
            print("Could not initialize data")

        if(data != ""): #The arduino loves to print garbage lines, I'm filtering them out here.
            count += 1
            try:
                data = int(data) #If its not int, its an error with a string (refer to arduino code)
                distance = round(data * sound/2, 3) #Distance in cm, rounded to 3 decimal points, (divide by two because the measured time is for the round trip)
                if(distance < MIN_DISTANCE_CM or distance > MAX_DISTANCE_CM): #Ignore garbage values, too close and too far
                    print("Filtered out value that is too close / too far")
                    error += 1
                    continue 
                
                print(f"{time.strftime('%H:%M:%S')} >  Distance: {distance} cm, Duration (time for sound to travel in microseconds): {data}") # Purely for my analysis, will remove later
                index = ((count - 1 - error) % sample) #We ignore the errors for index, count always goes up even when errors occur, so we must offset it
                sampleArray.append(distance)
                if(index == (sample - 1)):
                    arduino_data = data_organize(sampleArray)
                    arduino_data.update({"Temperature": temperature,
                                         "Duration": data})
                    write_data(arduino_data)
                    sampleArray = []
                                                  
            except ValueError:
                error += 1
                print(f"{time.strftime('%H:%M:%S')} > {data}") #This would print the error (Sound never returned and the sensor stopped waiting)
                continue
            
    print(f"Your total count was {count} and had {error} errors")
    ser.close()
    

def data_organize(sampleArray): 
    '''
    This function takes a packet of data values to be filtered, then returns a distance
    It works by taking the 25th quartile and the 75th quartile of the array, then finds how much
    the data is spread, by doing spread = 75th percentile - 25th percentile, the more the data is
    spread, the higher the value. We can calculate the boundary using the spread, boundary = spread *1.25,
    anything below sampleArray[i] < (median - boundary) is disregarded, anything above 
    sampleArray[i] > (median + boundary) is disregarded, this is a pretty good method of 
    getting rid of spikes / impossible jumps in the sensor.

    Parameters:
        sampleArray:    Array
                        The sample variable in config.ini decides how many data values
                        will be included in sampleArray for analysis
    Returns: All currently held data in a dict:
            {"Timestamp": time.strftime('%H:%M:%S'),
            "Raw Data": sampleArray,
            "Filtered Data": newArray,
            "Spread": spread,
            "Boundary": boundary,
            "Median": median,
            "Q2": twenty_five_Percentile,
            "Q3": seventy_five_Percentile,
            "Final Distance": mean
            } 
    '''

    sampleArray = sorted(sampleArray)
    itemsIndex = len(sampleArray) - 1
    mid = int(itemsIndex//2)
    if((itemsIndex + 1) % 2 == 0):
        median = (sampleArray[mid] + sampleArray[mid + 1]) / 2
    else:
        median = sampleArray[mid]
    
    twenty_five_Percentile = find_percentile(25, sampleArray)
    seventy_five_Percentile = find_percentile(75, sampleArray)
    spread = seventy_five_Percentile - twenty_five_Percentile #Find how much the data points in cm are spread near 50%
    boundary = spread * BOUNDARY_MULTIPLIER #Anything outside the boundary will be removed
    
    newArray = []
    mean = 0
    for i in range(itemsIndex + 1):
        if(sampleArray[i] <= (median + boundary) and sampleArray[i] >= (median - boundary)):
            newArray.append(sampleArray[i])
            mean += sampleArray[i]
    if(len(newArray) > 0): 
        print(f"Raw Data: {sampleArray}, Filtered Data: {newArray}, Spread: {spread}, Boundary: {boundary} Median: {median}, Quarter Percentile: {twenty_five_Percentile}, Third percentile: {seventy_five_Percentile}")
        mean = mean / len(newArray)
        print(f"Final Distance: {round(mean, 3)}")
    else:
        print("No valid data")

    return {"Timestamp": time.strftime('%H:%M:%S'),
            "Raw Data": sampleArray,
            "Filtered Data": newArray,
            "Spread": spread,
            "Boundary": boundary,
            "Median": median,
            "Q2": twenty_five_Percentile,
            "Q3": seventy_five_Percentile,
            "Final Distance": mean
            } 

def find_percentile(nthPercentile, sampleArray): #Will always be 25 and 75 percentile
    '''
    Simply finds the percentile of a sorted array

    Parameters:
        nthPercentile:  Int
                        Which percentile the program wants (25 and 75)

        sampleArray:    Array
                        The array sent to find the percentile of
    Returns: Percentile
    '''
    itemsIndex = len(sampleArray) - 1
    rank = (nthPercentile/100) * (itemsIndex) 
    rankInt = int(rank)
    rankFractional = rank - rankInt
    if(rank.is_integer()): Percentile = sampleArray[rankInt]
    else: Percentile = sampleArray[rankInt] + (rankFractional) * ((sampleArray[rankInt + 1]) - sampleArray[rankInt])
    return Percentile

def write_data(arduino_data):
    '''
    Writes data to a CSV file

    Parameters:
        arduino_data:   Dict 
                        All data written in a dict to process into a csv
    Returns: None
    '''
    headers = True
    exists = os.path.exists(CSV_FILE_NAME + ".csv")
    print(exists)
    if(exists): headers = False
    with open(CSV_FILE_NAME + ".csv", mode="a", newline="") as csvwriter:
        w = csv.DictWriter(csvwriter, arduino_data.keys())
        if(headers): w.writeheader()
        w.writerow(arduino_data)
    return

if __name__ == "__main__":
    serialize_arduino(config['arduino']['comport'],              #COMPORT
                     int(config['arduino']['baudrate']),        #BAUDRATE
                     int(config['arduino']['seconds']),         #SECONDS
                     int(config['arduino']['sample']),          #SAMPLE SIZE
                     int(config['arduino']['temperature']))     #TEMPERATURE OF ROOM
