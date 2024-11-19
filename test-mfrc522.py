#!/usr/bin/env python

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from mfrc522 import MFRC522
import time

GPIO.setwarnings(False)  # Disable GPIO warnings

# Function to check if the reader is detected initially and print reader details
def check_reader():
    mfrc522 = MFRC522()
    try:
        # Attempt to reset the reader to check if it's detected
        if not mfrc522.MFRC522_Reset():
            print("RFID Reader Detected Successfully")
            # Read version from the VersionReg register to get reader details
            version = mfrc522.MFRC522_Read(mfrc522.VersionReg)
            print(f"Reader Version: {hex(version)}")
            
            # Additional check for the type of MFRC522 reader
            if version == 0x91:
                print("Detected MFRC522 version 1")
            elif version == 0x92:
                print("Detected MFRC522 version 2")
            else:
                print("Unknown reader version")
        else:
            print("RFID Reader Detection Failed. Please check connections.")
            GPIO.cleanup()
            exit(1)  # Exit if reader detection fails
    except Exception as e:
        print(f"An error occurred: {e}")
        GPIO.cleanup()
        exit(1)

# Call the function to check if the reader is detected and get reader details
check_reader()

reader = SimpleMFRC522()

try:
    print("Waiting for RFID tag...")
    while True:
        # Wait for a tag and read the ID
        id, _ = reader.read()
        
        # Print the detected tag ID
        print(f"Tag ID: {id}")
        
        # Wait for a short time to avoid multiple reads of the same tag
        time.sleep(2)

finally:
    GPIO.cleanup()
