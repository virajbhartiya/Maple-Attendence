import face_recognition
import cv2
import numpy as np
import os
import pandas as pd
import time
import sys
import datetime
import requests
import threading
import ctypes
from openpyxl import load_workbook
from utils import clear, maximize_console
from printing import *
from db_maker import *



import warnings
warnings.filterwarnings("ignore", category=np.VisibleDeprecationWarning)

try:
    import tkinter as tk
    import tkinter.ttk as ttk
    from tkinter import filedialog
except ImportError:
    import Tkinter as tk
    import ttk
    import tkFileDialog as filedialog
from tkfilebrowser import askopendirname, askopenfilenames, asksaveasfilename


class Main:

    # Initialize some variables
    known_face_encodings = []
    known_face_roll_no = []
    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    attendance_record = set([])
    roll_record = {}

    # Rows in log file
    name_col = []
    roll_no_col = []
    timeIn_col = []

    # for updating
    refreshAt = "00"
    updateAfter = 0
    n = 2
    path = ""

    def __init__(self):
        # maximize_console()
        # ctypes.windll.kernel32.SetConsoleTitleW("Maple")
        # clear()
        # ctypes.windll.kernel32.SetFileAttributesW('F:\Maple\Cloud', 2)
        pass
    def verify(self, key):
        value = requests.get(
            "https://script.google.com/macros/s/AKfycbxR-GPuSkwpUeBm_mYLKQlkEGnhow5-fwQ4Y85KKrsnJfvGfWvCuoSEug/exec?num="+key).text
        if value == "\"Success\"":
            product = open("product.config", "w+")
            product.write(value)
        ctypes.windll.kernel32.SetFileAttributesW('F:\Maple\Cloud\config.config', 2)
        return value[value.index("\"")+1:value.rindex("\"")]

    def writeConfig(self):

        data = []
        data.append(input("At what time to refresh? (in 24hr format): ")+"\n")
        data.append(input(
            "After how many recongnitions do you want to update excel sheet? (Number): ")+"\n")
        print("Please selece a Directory where Photoes are saved")
        data.append(filedialog.askdirectory()+"\n")

        config = open("config.config", "w+")

        try:
            config.truncate(0)
        except:
            pass

        for i in range(len(data)):
            config.write(data[i])
        config.close()
        dbMaker(data[2][:data[2].index("\n")])
        self.path = data[2][:data[2].index("\n")]
        os.remove('student_db/people_db.xlsx')

    def readConfig(self):
        with open('config.config', 'r') as reader:
            data = reader.readlines()
            self.refreshAt = data[0]
            self.n = int(data[1])
            dbMaker(data[2][:data[2].index("\n")])
            self.path = data[2][:data[2].index("\n")]

    def strToBoolean(self, val):
        if val == "y" or val == "Y":
            return True
        elif val == "n" or val == "N":
            return False

    def updateDatabase(self):
        seperator = ","
        names = seperator.join(self.name_col)
        roll = seperator.join(str(self.roll_no_col))
        time = seperator.join(self.timeIn_col)
        resp = requests.get(
            f'https://script.google.com/macros/s/AKfycbyOMUi0Vh-_ZxNJZhqtWJl3_dz-mS5O213GMFyeb6l6fmw4b_4MMY7WLA/exec?key=update&names={names}&roll={roll}&time={time}').text
        
        if(resp != None):
            # if resp == "Success":
            self.updateAfter = 0
            # print("updated")
            # print(resp)
            pass
            # else:
            # print("\nOops... Something went wrong")

    def progressing(self):
        items = list(range(0, 67))
        for _ in progressBar(items, prefix='Progress:', suffix='Complete', length=50):
            time.sleep(0.1)

    def main(self):
        welcomeToFaceIt()
        logo()
        time.sleep(0.5)
        verified = False
        try:
            valu = ""
            with open('product.config', 'r') as reader:
                data = reader.readlines()
                val = data[0]
                if val != "\"Success\"":
                    key = input("Please enter your product Key: ")
                    valu = self.verify(key)
                else:
                    valu = "Success"
            ctypes.windll.kernel32.SetFileAttributesW('F:\Maple\Cloud\product.config', 2)
            if valu == "Success":
                verified = True
            elif valu == "Product Key in use":
                productKeyInUse()
                print()
                print("For reactivation Please contact: +91 84858 37871")
            elif valu == "Not found":
                invalidKey()
                verified = False

        except KeyboardInterrupt:
            pass
        except:
            key = input("Please enter your product Key: ")
            val = self.verify(key)
            if val == "Success":
                verified = True

        if verified:
            try:
                config = open('./config.config')
                readOrWrite = input(
                    "Do u want to use previous cofigurations?(Y or N): ")
                if readOrWrite == "Y" or readOrWrite == "y":
                    self.readConfig()
                else:
                    self.writeConfig()
                creatingDatabase()
            except KeyboardInterrupt:
                close()
                os._exit(1)
                pass

            except:
                self.writeConfig()
                creatingDatabase()

            # self.progressing()

            df = pd.read_excel("student_db" + os.sep + "output.xlsx")
            for _, row in df.iterrows():
                self.roll_no = row['Roll No']
                self.name = row['Name']
                self.image_path = row['Image']
                self.roll_record[self.roll_no] = self.name
                student_image = face_recognition.load_image_file(
                    "student_db" + os.sep + self.image_path)
                student_face_encoding = face_recognition.face_encodings(student_image)
                self.known_face_encodings.append(student_face_encoding)
                self.known_face_roll_no.append(self.roll_no)

            # Get a reference to webcam #0 (the default one)
            video_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            # A Nicer, Single-Call Usage
            print('-' * 50)
            print('{:<15s}{:<15s}{:<15s}{:<15s}'.format("Sr. No.","Names","Roll No.","Time"))
            print('-' * 50)
            try:
                while True :
                    # Grab a single frame of video
                    _, frame = video_capture.read()

                    # Resize frame of video to 1/4 size for faster face recognition processing
                    small_frame = cv2.resize(frame, (0, 0), fx=1, fy=1)

                    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
                    rgb_small_frame = small_frame[:, :, ::-1]

                    # Only process every other frame of video to save time
                    if self.process_this_frame:
                        # Find all the faces and face encodings in the current frame of video
                        self.face_locations = face_recognition.face_locations(
                            rgb_small_frame)
                        self.face_encodings = face_recognition.face_encodings(
                            rgb_small_frame, self.face_locations)

                        curr_time = time.localtime()
                        curr_clock = time.strftime("%H:%M:%S", curr_time)
                        # print(str(curr_clock[3:5]))
                        # print(curr_clock)
                        self.face_names = []
                        for face_encoding in self.face_encodings:
                            # See if the face is a match for the known face(s)
                            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
                            name = "Who u?"

                            # Or instead, use the known face with the smallest distance to the new face
                            face_distances = face_recognition.face_distance(
                                self.known_face_encodings, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                roll_no = self.known_face_roll_no[best_match_index]
                                # add this to the log
                                name = self.roll_record[roll_no]
                                if roll_no not in self.attendance_record:
                                    self.attendance_record.add(roll_no)
                                    print('{:<15d}{:<15s}{:<15d}{:<15s}'.format(len(self.name_col)+1,name,roll_no,curr_clock))
                                    # print('[+] ',name, roll_no, curr_clock)

                                    self.name_col.append(name)
                                    self.roll_no_col.append(roll_no)
                                    self.timeIn_col.append(curr_clock)

                                    self.updateAfter = self.updateAfter+1
                                    if curr_clock.startswith(self.refreshAt):
                                        self.name_col = []
                                        self.roll_no_col = []
                                        self.timeIn_col = []
                            self.face_names.append(name)

                    self.process_this_frame = not self.process_this_frame

                    # update the database
                    if self.updateAfter >= self.n:
                        # print("updating")
                        self.updateAfter = 0
                        thread = threading.Thread(target=self.updateDatabase)
                        thread.start()

                    # Display the results
                    for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):

                        # Draw a box around the face
                        cv2.rectangle(frame, (left, top),
                                    (right, bottom), (245, 214, 18), 2)

                        # Draw a label with a name below the face
                        cv2.rectangle(frame, (left, bottom - 35),
                                    (right, bottom), (245, 214, 18), cv2.FILLED)
                        font = cv2.FONT_HERSHEY_DUPLEX
                        cv2.putText(frame, name, (left + 6, bottom - 6),
                                    font, 1.0, (255, 255, 255), 1)

                    # Display the resulting image
                    cv2.imshow('Webcam', frame)

                    # Hit 'q' on the keyboard to quit!
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        close()
                        break
            except KeyboardInterrupt:
                close()
                self.updateDatabase()
            # self.updateExcel()
            self.updateDatabase()
            video_capture.release()
            cv2.destroyAllWindows()

        else:
            print("Software Not activated... Try Again or contact: +91 84858 37871")


app = Main()
try:
    app.main()
except KeyboardInterrupt:
    close()
    app.updateDatabase()
    os._exit(1)


# https://script.google.com/macros/s/AKfycbyOMUi0Vh-_ZxNJZhqtWJl3_dz-mS5O213GMFyeb6l6fmw4b_4MMY7WLA/exec?key=update&names=['Viraj','Dua']&roll=['9','5']&time=[5:5:5,5:5:5]
