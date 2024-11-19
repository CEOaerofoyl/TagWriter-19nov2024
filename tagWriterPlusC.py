#!/usr/bin/env python3

import os
import time
from barcode import EAN13
from barcode.writer import ImageWriter
import qrcode
import pyrebase
from lib.waveshare_epd import epd2in9
from PIL import Image, ImageDraw, ImageFont
from includes.text import Text
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import subprocess
import urllib.request
import socket

def is_internet_available():
    try:
        urllib.request.urlopen('http://www.google.com', timeout=1)
        return True
    except urllib.error.URLError:
        return False
    except socket.timeout:
        return False


# @reboot cd /home/sky/TagWriterCode/ && /usr/bin/python3 /home/sky/TagWriterCode>

mylist = []
LnameList = []
FnameList = []
dateList = []
toAptList = []
flightList = []
PNRList = []
SEQList = []
script_dir = os.path.dirname(os.path.abspath(__file__))
pic_dir = os.path.join(script_dir,'pic') # Points to pic directory .

def resourcePath(filename):
    return os.path.join(script_dir,filename)


def get_data_generate_barcode(line):
    print("Generating barcode...")
   #Walks through each line
    data= line.split(',')
    print(data[0])
    code = EAN13(data[0], writer=ImageWriter()) 
    filename = code.save(resourcePath(data[0].strip()))        #Saves Line 'tnumfile' as filename
    
    qrImg = qrcode.make(data[0])
    type(qrImg)
    qrImg.save(resourcePath(data[0].strip()+"_qr.png"))
    
    mylist.insert(0,data[0].strip() )
    LnameList.insert(0,data[1])
    FnameList.insert(0,data[2])
    dateList.insert(0,data[3])
    toAptList.insert(0,data[4])
    flightList.insert(0,data[5])
    PNRList.insert(0,data[6])
    SEQList.insert(0,data[7].strip())
        
def make_image_and_write():
    i=0
    try:
        for item in mylist:
            name= LnameList[i]+" / " + FnameList[i]
            details= "B / W : 1 / 13"
            pnr="PNR: "+PNRList[i]
            date= dateList[i]
            date=date[0:10]
            toApt=toAptList[i]
            flight=flightList[i]
            SEQ="SEQ : " + SEQList[i]
            fntsize=35
            fnt = ImageFont.truetype(resourcePath("ZenDots-Regular.ttf"), fntsize)
            im = Image.new('L',(293,127),color=(255))


            d = ImageDraw.Draw(im)
        #   nameLength= int(d.textlength(name,font=fnt))+40
            d.text((30,1),name,font = ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 16), fill=(0))
            d.text((30,17),pnr, font = ImageFont.truetype(resourcePath("fonts/Roboto-Regular.ttf"), 12), fill=(0))
            d.text((210,2),details, font = ImageFont.truetype(resourcePath("fonts/Roboto-Regular.ttf"), 12), fill=(0))
            d.text((210,15),date, font =  ImageFont.truetype(resourcePath("fonts/Roboto-Regular.ttf"), 12), fill=(0))
            d.text((55,110),mylist[i],font = ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 15), fill=(0))

            im2 = Image.new('1',(127,25),color=(0))
            d1 = ImageDraw.Draw(im2)
            d1.text((28,1),SEQ, font=ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 18), fill=(255))
            im.paste(im2.transpose(Image.ROTATE_90),(0,0))
            
            im2 = Image.new('1',(70,18),color=(255))
            d1 = ImageDraw.Draw(im2)
            d1.text((28,0),toApt, font=ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 18), fill=(0))
            im.paste(im2.transpose(Image.ROTATE_90),(255,46))
            
            im2 = Image.new('1',(80,18),color=(255))
            d1 = ImageDraw.Draw(im2)
            d1.text((28,0),flight, font=ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 14), fill=(0))
            im.paste(im2.transpose(Image.ROTATE_90),(275,41))

            barcodeImage= Image.open(resourcePath(mylist[i]+ '.png'))
            bc_cropped= barcodeImage.crop((64,0,490,190))
            bc_scaled = bc_cropped.resize((190,80))    
            im.paste(bc_scaled,(25,30))
            
            qrImage= Image.open(resourcePath(mylist[i]+ '_qr.png'))
            qr_cropped= qrImage.crop((30,30,280,280))
            qr_scaled = qr_cropped.resize((60,60))    
            im.paste(qr_scaled,(200,45))
    #         im.save('ticket'+ str(i) + '.png')
            
        # d.text(((343-d.textlength(toApt, font = fnt))/2,650),toApt, font = ImageFont.truetype("ZenDots-Regular.ttf", 40), fill=(0,0,0))
        # d.text(((343-d.textlength(flight, font = fnt))/2,700),flight, font = ImageFont.truetype("ZenDots-Regular.ttf", 40), fill=(0,0,0))
            im_rot = im.transpose(Image.ROTATE_90)
            im_scale=im_rot.resize((127,293))
            im_rot=im_rot.convert('1', dither=Image.NONE)
            im_rot.save(resourcePath('pic/fimage.bmp'))
            ep = resourcePath('epd')
            subprocess.run(['sudo',ep],check=True)
            
            print('generating ticket...')
            os.remove(resourcePath(mylist[i]+ '_qr.png'))
            os.remove(resourcePath(mylist[i]+ '.png'))
            
        # Display init, clear
    
        data = {
        "Online_Status": "1",
        "Writing_status" :"1"
        }
        
        #db.child("Writer_Status").child("DID001").set(data)
        print(data)
        print("Done...")
    except IOError as e:
        print(e)
        
try:


    reader = SimpleMFRC522()
    loop=True
    #guid="123456789"
    init="1"
    while(loop):

        
        
        print("Waiting for new ticket...("+str(init)+")")
        if(init=="1"):
            bagNos="1"
            if(bagNos=='noofBaggage'):
                print("Clear Command to execute")
                ep = resourcePath('epdClean')
                subprocess.run(['sudo',ep],check=True)
            else:
                print("No of tags to be generated: " + bagNos)
                for tagNo in range(1,int(bagNos)+1):
                    
                    try:
#                          print("Place a tag on the writer...")
#                          id, text = reader.read()
#                          
#                          guid = id
#                          print("GUID: " + str(guid))

                         guid =123
                         print("bypass mfrc done")
                    finally:
                        GPIO.cleanup()
                        
#                     init=db.child("tagWriter").child("DID002").child("guid").child(tagNo).set(guid)
                    data="0232789879902,Farooq,Bhat,2024-02-05T11:45:23.714Z,BOM,6A723,FP7V1,167"
                    print(data)
                    get_data_generate_barcode(data)
                    make_image_and_write()
        init="0"
        time.sleep(0.5)

except KeyboardInterrupt:
    # This block will be executed when Ctrl+C is pressed
    print("Script interrupted by user. Performing cleanup...")
    GPIO.cleanup()

except Exception as e:
    # This block will be executed in case of any other exception
    print(f"An error occurred: {str(e)}")
    GPIO.cleanup()

finally:
    # This block will be executed regardless of whether there was an exception or not
    print("Exiting script. Performing final cleanup...")
    GPIO.cleanup()