from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
from barcode import EAN13
from barcode.writer import ImageWriter
import qrcode
import subprocess
from lib.waveshare_epd import epd2in9
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import urllib.request
import socket

app = Flask(__name__)
CORS(app)

mylist = []
LnameList = []
FnameList = []
dateList = []
toAptList = []
flightList = []
PNRList = []
SEQList = []
script_dir = os.path.dirname(os.path.abspath(__file__))
pic_dir = os.path.join(script_dir, 'pic')  # Points to pic directory.

def resourcePath(filename):
    return os.path.join(script_dir, filename)

def get_data_generate_barcode(line):
    print("Generating barcode...")
    data = line.split(',')
    code = EAN13(data[0], writer=ImageWriter())
    filename = code.save(resourcePath(data[0].strip()))  # Saves Line 'tnumfile' as filename

    qrImg = qrcode.make(data[0])
    qrImg.save(resourcePath(data[0].strip() + "_qr.png"))

    mylist.insert(0, data[0].strip())
    LnameList.insert(0, data[1])
    FnameList.insert(0, data[2])
    dateList.insert(0, data[3])
    toAptList.insert(0, data[4])
    flightList.insert(0, data[5])
    PNRList.insert(0, data[6])
    SEQList.insert(0, data[7].strip())
    return data[0]

def make_image_and_write():
    i = 0
    try:
        for item in mylist:
            name = LnameList[i] + " / " + FnameList[i]
            details = "B / W : 1 / 13"
            pnr = "PNR: " + PNRList[i]
            date = dateList[i][0:10]
            toApt = toAptList[i]
            flight = flightList[i]
            SEQ = "SEQ : " + SEQList[i]
            im = Image.new('L', (293, 127), color=(255))

            d = ImageDraw.Draw(im)
            d.text((30, 1), name, font=ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 16), fill=(0))
            d.text((30, 17), pnr, font=ImageFont.truetype(resourcePath("fonts/Roboto-Regular.ttf"), 12), fill=(0))
            d.text((210, 2), details, font=ImageFont.truetype(resourcePath("fonts/Roboto-Regular.ttf"), 12), fill=(0))
            d.text((210, 15), date, font=ImageFont.truetype(resourcePath("fonts/Roboto-Regular.ttf"), 12), fill=(0))
            d.text((55, 110), mylist[i], font=ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 15), fill=(0))

            im2 = Image.new('1', (127, 25), color=(0))
            d1 = ImageDraw.Draw(im2)
            d1.text((28, 1), SEQ, font=ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 18), fill=(255))
            im.paste(im2.transpose(Image.ROTATE_90), (0, 0))

            im2 = Image.new('1', (70, 18), color=(255))
            d1 = ImageDraw.Draw(im2)
            d1.text((28, 0), toApt, font=ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 18), fill=(0))
            im.paste(im2.transpose(Image.ROTATE_90), (255, 46))

            im2 = Image.new('1', (80, 18), color=(255))
            d1 = ImageDraw.Draw(im2)
            d1.text((28, 0), flight, font=ImageFont.truetype(resourcePath("fonts/Roboto-Bold.ttf"), 14), fill=(0))
            im.paste(im2.transpose(Image.ROTATE_90), (275, 41))

            barcodeImage = Image.open(resourcePath(mylist[i] + '.png'))
            bc_cropped = barcodeImage.crop((64, 0, 490, 190))
            bc_scaled = bc_cropped.resize((190, 80))
            im.paste(bc_scaled, (25, 30))

            qrImage = Image.open(resourcePath(mylist[i] + '_qr.png'))
            qr_cropped = qrImage.crop((30, 30, 280, 280))
            qr_scaled = qr_cropped.resize((60, 60))
            im.paste(qr_scaled, (200, 45))

            im_rot = im.transpose(Image.ROTATE_90)
            im_scale = im_rot.resize((127, 293))
            im_rot = im_rot.convert('1', dither=Image.NONE)
            im_rot.save(resourcePath('pic/fimage.bmp'))
            ep = resourcePath('epd')
            subprocess.run(['sudo', ep], check=True)

            print('Generating ticket...')
            os.remove(resourcePath(mylist[i] + '_qr.png'))
            os.remove(resourcePath(mylist[i] + '.png'))

        print("Done...")
    except IOError as e:
        print(e)

@app.route('/printTags', methods=['POST'])
def print_tags():
    try:
        content = request.get_json()
        data = content['data']
        init = content['init']
        num_bags = int(content['numBags'])

        if init == "1":
            print(f"Number of tags to be generated: {num_bags}")
            printed_guids ={}
            for tag_no in range(1, num_bags + 1):
                guid = 123  # Dummy GUID for now
                print(f"Generating tag for GUID: {guid}")
                lpn = get_data_generate_barcode(data)
                printed_guids[lpn]=guid
                make_image_and_write()
        else:
            print("Init is not 1, skipping tag generation.")

        return jsonify({"status": "success","guids":printed_guids}), 200
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/cleanTag', methods=['GET'])
def clean_tag():
    try:
        print("Clear Command to execute")
        ep = resourcePath('epdClean')
        subprocess.run(['sudo', ep], check=True)
        return jsonify({"status": "success", "message": "Tags cleaned successfully."}), 200
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/19', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "message": "Server is running."}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5478, debug=True)
