"""
Code used for targeting system of the print head spray system.
Code initially developed 2023 by Wesley Moss
Utilises opencv for colour detection. Does NOT use YOLO plant detection model
Refer to Github for further details https://github.com/precision-sustainable-ag/precision-spray/
"""
import cv2
import numpy as np
import time
import imutils
import tkinter as tk
from PIL import Image, ImageTk
from math import *
from pymodbus.client import ModbusTcpClient
from arena_api.system import system
import multiprocessing
from datetime import datetime

"""Physical Calibration"""
pixToMeters = 0.24/(739-51)#0.1/(320-215)#(9*0.0254)/(355-117.5)#(10*0.0254)/(475-185)   # ratio of  m to pixels in the actual frame, m/pix
centframePos = 0.25775  # distance from centre of frame to valves, m
sliderWidthDefault = 213.5 #Width of the columns that correspond to valve position
sliderCentreDefault = 0 #Adjusts the centre of the columns that align with the valves

'''Flash on/off'''
flash = True #Flag for turning the flash on and off. Manually change in code before running to turn flash on/off
if flash:
    exposure_time = 500.0 #camera exposure time
    gain_db = 3.0 #camera gain
else:
    exposure_time = 18000.0 #camera exposure time
    gain_db = 19.0 #camera gain

'''Default settings'''
valveTime = 5 # default valve open time, ms
camHeight = 1344 #height of image after processing
camWidth = 896 # width of image after processing #int((cropSize/3000)*camHeight)
cropSize = int(camWidth*3000/camHeight) # size to initially crop width to. 
sliderVelocityDefault = (0.19+0.064+0.002) # vehicle speed in m/s
frameLength = camHeight*pixToMeters # length of the frame in direction of travel, mchecks if PLC is connected
client = ModbusTcpClient('169.254.229.134') #initialise modbus at assigned IP
hozLineLocDefault = camHeight/2 # position of horizontal line that triggers the valve firing
sliderThresLowDefault =90 # lower threshold of the countour area that is shown with a circle and used to fire
sliderThresUppDefault = 11080 # upper threshold of the countour area that is shown with a circle and used to fire
rowCount = 32 +1 # number of rows corresponding to the number of nozzles
fireBool = False # flag to control the "Fire" button
squareBool = False #flag to control if a sqaure pattern is fired
slideDelayDefault = -5 # Time delay on firing. -5ms default to account for lag in firing
slideVOffsetDefault = 0 # Offset on the velocity
sliderPixDefault = 5 
sliderBufferDefault = 230
sliderFPSDefault = 4#  1.5*sliderVelocityDefault/frameLength 
sliderSquareDefault = 3     # default size of sqaure firing pattern
sliderSquareSpacingDefault = 10 # 
sliderHDefault = 50
sliderSDefault = 37
sliderVDefault = 50


gridBool = True # toggles grids in image on and off
recordBool = False # toggles recoridng of images on and off
getPixelColor = False   # flag to get the pixel color when needed

H, S, V = 47, 156, 177   # the color properties of the Pixel to track. Iniitalises as yellow
mouseX, mouseY = 0, 0   # declare variables to capture mouse position for color tracking

x, y = 0, 0 

controllerWindow = tk.Tk()  # initializes this tk interpreter and creates the root window
controllerWindow.title("Quantum Sprinkler - Colour Detection")    # define title of the root window
controllerWindow.geometry("700x700+50+50")    # define size of the root window
controllerWindow["bg"] = "lightgrey"     # define the background color of the root window
controllerWindow.resizable(0, 0)    # define if the root window is resizable or not for Vertical and horizontal

'''Initialises GUI Windows'''
videoWindow = tk.Toplevel(controllerWindow)     # a new window derived from the root window "controllerwindow"
videoWindow.title("Camera") 
videoWindow.geometry(str(camWidth)+"x"+str(camHeight)+"+50+50")#("820x600+50+50")   # define title of videowindow
videoWindow.resizable(0, 0)  # Cannot resize the window
lmain = tk.Label(videoWindow)   #create an empty label widget in the videoWindow
lmain.pack()    # adjust the size of the videowindow to fit the label lmain
videoWindow.withdraw()  # hide the window
showVideoWindow = False
showColourWindow = False

'''System functions'''
def testShot():  # Fires all of the valves
    global coil_array
    for i in range(len(coil_array)):
          #print("Fire all")
              try: 
                  client.write_coil(coil_array[i], True)
              except:
                  print("Misfire ",i+1)

def create_devices_with_tries(): # Creates device for the Lucid Camera
    
    device_infos = None
    selected_index = None
    while selected_index is None:
        device_infos = system.device_infos
        if len(device_infos) == 0:
            print("No camera connected\nPress ent=er to search again")
            input()
            continue
        print("Devices found:")
        for i in range(len(device_infos)):
            print(f"\t{i}. {device_infos[i]['model']} SN: {device_infos[i]['serial']}")

        while True:
            line = 0
            try:
                selected_index = int(line)
                if 0 <= selected_index < len(device_infos):
                    break
                else:
                    print(f"Please enter a valid number between 0 and {len(device_infos)-1}\n")
            except Exception as e:
                print("\nPlease enter a valid number\n")

    selected_model = device_infos[selected_index]['model']
    print(f"\nCreate device: {selected_model}...")
    device = system.create_device(device_infos=device_infos[selected_index])[0]
    
    return device

def getMouseClickPosition(mousePosition):   # get mouse click position
    global mouseX, mouseY
    global getPixelColor
    mouseX, mouseY = mousePosition.x, mousePosition.y
    print("mouse",mouseX,mouseY)
    getPixelColor = True


def showCameraFrameWindow():    # function to toggle the showVideoWindow and change the label text of the button
    global showVideoWindow
    
    if showVideoWindow == False:
        
        videoWindow.deiconify()
        showVideoWindow = True
        BShowVideo["text"] = "Hide Live Video Feed"
    else:
        videoWindow.withdraw()
        showVideoWindow = False
        BShowVideo["text"] = "Show Live Video Feed"

def showColourCorrectedWindow():    # function to toggle the showCouolurWindow and change the label text of the button
    global showColourWindow
    if showColourWindow == False:
    
        #colourWindow.deiconify()
        showColourWindow = True
        BColourVideo["text"] = "Hide Colour Filter"
    else:
        #colourWindow.withdraw()
       showColourWindow = False
       BColourVideo["text"] = "Show Colour Filter"
       cv2.destroyAllWindows()

def setValveTime(t): #t in ms
    status = False
    for i in range(5):
            
            try:
                client.write_register(0,int(t)) # sets PLC valve open time to valveOpenTime in ms
                print("Valve open time set to ",t)
                status = True
                break
            except:
                print("Valve open time failed, count ",i+1)
    return(status)

def valveOpenTime():
    global valveTime
    if valveTime == 5:
        valveTime = 10
        success = setValveTime(valveTime)
        if success:
            label.configure(text="Valve Open Time 10ms", fg="red")
    elif valveTime == 10:
        valveTime = 20
        success = setValveTime(valveTime)
        if success:
            label.configure(text="Valve Open Time 20ms", fg="red")
    elif valveTime == 20:
        valveTime = 30
        success = setValveTime(valveTime)
        if success:
            label.configure(text="Valve Open Time 30ms", fg="red")
    elif valveTime == 30:
        valveTime = 5
        success = setValveTime(valveTime)
        if success:
            label.configure(text="Valve Open Time 5ms", fg="red")

def fireToggle(): #toggles the Fire Bool
    global fireBool
    global label
    global BFire
    if fireBool:
        fireBool = False
        
        BFire["text"] = "Fire"
    else: 
        fireBool = True
        BFire["text"] = "Fire Off"
        #label.configure(text="Fire On", fg="#36db8b")
        

def squareToggle(): # toggles square firing pattern flag on and off 
    global squareBool
    if squareBool:
        squareBool = False
        BSquare["text"] = "Square pattern"

    else:
        squareBool = True
        BSquare["text"] = "Single shot"

def recordFire(): #toggles the recording Bool
    global recordBool

    if recordBool:
        recordBool = False
        
        BRecord["text"] = "Record On"
    else: 
        recordBool = True
        BRecord["text"] = "Record Off"

def endProgam():        # function to close root window
    try:
        devices.stop_stream()
        system.destroy_device()
    except:
        print("No camera device to terminate")

    controllerWindow.destroy()
    cv2.destroyAllWindows()
    p1.terminate()

def gridToggle(): # toggles grid lines on and off in the image
    global gridBool
    if gridBool:
        gridBool = False
    else:
        gridBool = True


start_time = time.time()

def plcConnect(): # connects to PLC
    plc_res = client.connect() #checks if PLC is connected
    if plc_res:
       print("Connected to PLC")
    else: 
        print("No connection to PLC")

def donothing():    # function that does nothing
    pass

def fire(nn):  #function to trigger valves in print head.  fire(nn) triggers valve nn+1. 
    global coil_array
    
    try:
        client.write_coil(coil_array[(nn)], True)
        #print("FIRE ROW",(nn+1))
        #print(time.time())
        
    except:
        try:
            client.write_coil(coil_array[(nn)], True)
            #print("FIRE ROW",(nn+1))
        except:
            print("Misfire ",nn)

coil_array = [] # array of modbus addresses for each valve output on the PLC. 
def gen_array():
    global coil_array
    for i in range(8224,8232):
        coil_array.append(i)
    for i in range(8256,8264):
        coil_array.append(i)
    for i in range(8288,8296):
        coil_array.append(i)
    for i in range(8320,8328):
        coil_array.append(i)

gen_array() #populates coil_array

fire_array = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]

def calibration(c): #calibration to account for positional errors from devications in vavlves
    #200mm height. Calibration on 23-10-11
    dist_offset = 0
    if c == 1:
        dist_offset=3.0/1000
    # if c ==3:
    #     c=4 #use valve 5 (4+1) instead of valve 4 (3+1)
    if c ==7:
        c=8 #use valve 9 (8+1) instead of valve 8 )7+1)
    if c ==9:
        dist_offset=-2.0/1000
    if c==15:
        c=16 #use next valvle instead
    if c == 19:
        c = 20
    if c == 20:
         dist_offset=-5.0/1000
    if c == 23:
         c=24
    return(c, dist_offset)


def fireStore(c,y,ttime,q): # stores recent fire commands so they can be applied with a delay
    global fire_array, start_time
    vOffset= sliderVOffset.get()
    pixOffset = sliderPixOffset.get()/100000
    delay = sliderDelay.get()/1000.0
    vVel = sliderVelocity.get()
    #ctime = time.time()
    c, dist_offset = calibration(c) #adjusts due to misalignments in valves
    dist = ((pixToMeters+pixOffset)*((camHeight/2)-y))+centframePos+dist_offset # distance between object and valve, m
    travTime = (dist/(vVel+vOffset))+delay # travel time between object and valve given vVel
    q.put([c,ttime+travTime, False])


def fireSquare(i,y,ttime,q): # stores a square of fire commands 
    global fire_array, start_time
    sqSize = int(sliderSquare.get())
    sqDelay = sliderSquareSpacing.get()/1000.0 # delay between sqaure firings
    vOffset= sliderVOffset.get()
    pixOffset = sliderPixOffset.get()/100000
    delay = sliderDelay.get()/1000.0
    vVel = sliderVelocity.get()
    
    dist = ((pixToMeters+pixOffset)*((camHeight/2)-y))+centframePos # distance between object and valve, m
    travTime = (dist/(vVel+vOffset))+delay # travel time between object and valve given vVel
    if sqSize %2 != 0:
        
        for d in range(int(1-((sqSize+1)/2)),int((sqSize+1)/2)):
            for r in range(int(1-((sqSize+1)/2)),int((sqSize+1)/2)):
                row = i + r
                #print("square", row)
                if row >= 0 and row<=31:
                    q.put([row,ttime+travTime + (d*sqDelay),True])
                    #print("put in queue,", i, d)
    else:
        for d in range(1-(sqSize)/2,(sqSize)/2):
            for row in range(1-(sqSize)/2,(sqSize)/2):
                i = i + row
                if i >= 0 and i<=31:
                    q.put([i,ttime+travTime + (d*sqDelay), True])


def doubleUpCheck(c,TT): #checks to see if there is a double up of times in adjacent columns
    check = True
    lowerBound = c-2 #two columns below and above will be checked
    upperBound = c+3
    if lowerBound < 0:
        lowerBound = 0
    if upperBound> 32:
        upperBound = 32

    for i in range(lowerBound,upperBound):
        if len(fire_array[i]) >0:
                for r in range(len(fire_array[i])):
                    t = fire_array[i][r]
                    if abs(t-TT)<0.01:
                        check = False # There is a double up
                        #print("double up detected")
                        break
    return check 


def multiProcessFireCheck(q):  #In a sperate process, gets travel time from queue, q, and checks if it should fire a valve
    while True:
        loopStart = time.time()
        try:
            val = q.get(block = False)
            c = val[0] #column to fire
            TT = val[1] # time transferred from the queue
            squareFlag = val[2] #flag of whether a sqaure firing sequence
            if not squareFlag:
                if doubleUpCheck(c,TT):
                    fire_array[c].append(TT) #only saves to array if doubleUpCheck shows there isn't a doubelup
            else:
                fire_array[c].append(TT)
            #print("received from queue")
        except:
                pass
        current_time = time.time()
        for i in range(32):
            if len(fire_array[i]) >0:
                for r in range(len(fire_array[i])):
                    try:
                        t = fire_array[i][r]
                        #print((current_time - t)>=delay)
                        if ((current_time - t)>=0):
                            fire(i)
                            #print("fire command")
                            fire_array[i].pop(r)
                            if ((current_time - t)>0.008):
                                print('Delayed firing: ',i,current_time - t)
                            break # break loop looking at this row as one was already found to fire this time
                    except:
                        t = 0

FrameTime = time.time()

kernel = np.ones((6, 6), np.uint8) # used of for dilation and erosion

def main():     # declaring the main function of the program
    
    global H, S, V
    global getPixelColor
    global x, y
    global camWidth, camHeight
    global start_time
    global showVideoWindow
    global FrameTime
    global q, gridBool
     
    targetFPS = sliderFPS.get()
    if targetFPS !=0:
        TimeTarget = 1/targetFPS
    
        if (time.time()- FrameTime) >= TimeTarget:
            #print("FPS ", 1.0/ (time.time()- FrameTime))
            triggerFlag = False # flag to see if a trigger was sensed in this frame
            FrameTime = time.time()
            nodemap['TriggerSoftware'].execute()
            image_buffer = devices.get_buffer()  # optional args
            img = np.ctypeslib.as_array(image_buffer.pdata,shape=(image_buffer.height, image_buffer.width, int(image_buffer.bits_per_pixel / 8))).reshape(image_buffer.height, image_buffer.width, int(image_buffer.bits_per_pixel / 8))
            
            crop = 800
            height = img.shape[0]
            width = img.shape[1]
            dim = (camWidth, camHeight)
           
            img = cv2.cvtColor(img, cv2.COLOR_BayerBG2BGR)
            img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
            imgHSV = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            if getPixelColor == True: #gets posotion of mouse click
                    pixelColorOnClick = img[mouseY, mouseX]
                    pixelColorOnClick = np.uint8([[pixelColorOnClick]])
                    pixelColorOnClick = cv2.cvtColor(pixelColorOnClick, cv2.COLOR_BGR2HSV)
                    H = pixelColorOnClick[0, 0, 0]
                    S = pixelColorOnClick[0, 0, 1]
                    V = pixelColorOnClick[0, 0, 2]
                    print("New colour", H, S, V)
                    getPixelColor = False
            
            lowerBound = np.array([H - sliderH.get(), S - sliderS.get(), V - sliderV.get()])
            upperBound = np.array([H + sliderH.get(), S + sliderS.get(), V + sliderV.get()])

            mask = cv2.inRange(imgHSV, lowerBound, upperBound)
            mask = cv2.blur(mask, (6, 6))  # Blur mask
            mask = cv2.erode(mask, kernel, iterations=1)  #  mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, kernel, iterations=1)  #  mask = cv2.dilate(mask, None, iterations=2)

                    
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,  
                                    cv2.CHAIN_APPROX_SIMPLE)  # added wes 13-06 to try increase cicrlce stability
            cnts = imutils.grab_contours(cnts)  # wes 
            center = None
                    
            height = img.shape[0]
            width = img.shape[1]
            width_gap = sliderWidth.get()
            centreOffset = sliderCentre.get()
            buffer = sliderBuffer.get()
            rowWidth = (width - (2*width_gap)) / rowCount
            
            if gridBool and showVideoWindow:
                cv2.line(img, (0, sliderHoz.get()), (width, sliderHoz.get()), (255, 0, 0), 2) # horizontal line
                cv2.line(img, (0, sliderHoz.get()+buffer), (width, sliderHoz.get()+buffer), (255, 0, 0), 1) # Upper buffer line
                cv2.line(img, (0, sliderHoz.get()-buffer), (width, sliderHoz.get()-buffer), (255, 0, 0), 1) # Lower buffer line
                for i in range(rowCount): #generates strips of vertical lines
                    cv2.line(img, (int(width_gap + centreOffset+ (i*rowWidth)), 0), (int(width_gap + centreOffset + (i*rowWidth)), height), (255, 0, 0), 2) # vertical line
            
            HozPos = sliderHoz.get()
            threshold_low = sliderThresLow.get()
            threshold_upp = sliderThresUpp.get()
            
           
            
            if len(cnts) > 0:
                for i in range(len(cnts)):
                    M = cv2.moments(cnts[i])
                    
                    try:
                        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                        x, y = center
                        area = cv2.contourArea(cnts[i])
                
                        if area>threshold_low and area < threshold_upp:
                            cv2.circle(img, (int(x), int(y)), int(1), (0, 0, 0), 2)
                            
                            if fireBool: # check if the fire bool is on
                                
                            
                                if ((HozPos- buffer) < y < (HozPos+ buffer)): # checks if it is at the horizntal line
                                    for i in range(rowCount-1): #checks which row it is in
                                        if (width_gap  + centreOffset+ (i*rowWidth)) <= x < (width_gap  + centreOffset+ ((i+1)*rowWidth)):
                                            #print("FIRE ROW",(i+1))
                                            i = 31-i # inverting row
                                            if squareBool:
                                                fireSquare(i,y,FrameTime,q) #sqaure pattern
                                            else:
                                                fireStore(i,y,FrameTime,q) #single pattern
                                                #print("stored ",i)
                                            cv2.circle(img, (int(x), int(y)), int(1), (0, 0, 255), 3) #red circle around the firing object
                                            cv2.putText(img, str(i+1), (int(x) + 10, int(y) +10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                                            triggerFlag = True
                                           
                                            #print('Trigger: ',i, y, FrameTime)
                        
                    except:
                        pass
                    
            if showVideoWindow == True: #window showing the live camera feed
                imgV = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) 
                trans_img = Image.fromarray(imgV)
                imgtk = ImageTk.PhotoImage(image=trans_img)
                lmain.imgtk = imgtk
                lmain.configure(image=imgtk)

        
            if showColourWindow == True: #window showing the colour mask feed
               
                cv2.imshow("Frame", mask)    
                        
                    
               
            if recordBool and triggerFlag: # records the current frame   
                current_time = datetime.now().astimezone()
                
                time_string = current_time.isoformat(timespec="milliseconds")
                time_string = time_string.replace('+','_')
                time_string = time_string.replace(':','_')
                filename = f'Recordings/spray_record_{time_string}.jpg'
                cv2.imwrite(filename, img)
        
            devices.requeue_buffer(image_buffer) 
    
    lmain.after(5, main)

   

'''Below code defines the function and layout of the TKinter GUI '''

FrameVideoControl = tk.LabelFrame(controllerWindow, text="Video Control")
FrameVideoControl.place(x=20, y=20, width=380)
EmptyLabel = tk.Label(FrameVideoControl)
EmptyLabel.pack()
BShowVideo = tk.Button(FrameVideoControl, text="Show Live Video Feed", command=showCameraFrameWindow)
BShowVideo.place(x=100, y=-5)

sliderH = tk.Scale(controllerWindow, from_=0, to=100, orient="horizontal", label="H", length=95,
                   tickinterval=10)
sliderH.set(sliderHDefault)
sliderH.place(x=20, y=80, width=120, height=60)
sliderS = tk.Scale(controllerWindow, from_=0, to=100, orient="horizontal", label="S", length=95,
                   tickinterval=10)
sliderS.set(sliderSDefault)
sliderS.place(x=150, y=80, width=120, height=60)
sliderV = tk.Scale(controllerWindow, from_=0, to=100, orient="horizontal", label="V", length=95,
                   tickinterval=10)
sliderV.set(sliderVDefault)
sliderV.place(x=280, y=80, width=120, height=60)

sliderSquare=tk.Scale(controllerWindow, from_=3, to=15, orient="horizontal", label="Square Size", length=1000, tickinterval=2,
                       resolution=2)
sliderSquare.place(x=20, y=150, width=180, height=60)
sliderSquare.set(sliderSquareDefault)

BSquare = tk.Button(controllerWindow, text="Square Pattern", command=squareToggle, background="white")
BSquare.place(x=100, y=150)

sliderSquareSpacing=tk.Scale(controllerWindow, from_=1, to=100, orient="horizontal", label="Square Spacing", length=1000, tickinterval=1,
                       resolution=1)
sliderSquareSpacing.place(x=210, y=150, width=180, height=60)
sliderSquareSpacing.set(sliderSquareSpacingDefault)

sliderVelocity=tk.Scale(controllerWindow, from_=0, to=3, orient="horizontal", label="Vehicle Velocity", length=1000, tickinterval=0.01,
                       resolution=0.001)
sliderVelocity.place(x=20, y=220, width=360, height=60)
sliderVelocity.set(sliderVelocityDefault)

sliderHoz = tk.Scale(controllerWindow, from_=0, to=camHeight, orient="horizontal", label="Horizontal Line Offtset", length=95, tickinterval=1,
                       resolution=1)
sliderHoz.place(x=20, y=290, width=180, height=60)
sliderHoz.set(hozLineLocDefault)

sliderBuffer = tk.Scale(controllerWindow, from_=0, to=camHeight/2, orient="horizontal", label="Buffer", length=95, tickinterval=5,
                       resolution=5)
sliderBuffer.place(x=210, y=290, width=180, height=60)
sliderBuffer.set(sliderBufferDefault)

BFire = tk.Button(controllerWindow, text="Fire", command=fireToggle, background="white")
BFire.place(x=20, y=360)

BPLC_Connect = tk.Button(controllerWindow, text="PLC Check", command=plcConnect, background="white")
BPLC_Connect.place(x=75, y=360)

BOpenTime = tk.Button(controllerWindow, text="Set Valve Time", command=valveOpenTime, background="white")
BOpenTime.place(x=150, y=360)

BQuit = tk.Button(controllerWindow, text="Quit", command=endProgam, background="red")
BQuit.place(x=360, y=360)

BColourVideo = tk.Button(controllerWindow, text="Show Colour Filter", command=showColourCorrectedWindow)
BColourVideo.place(x=20, y=420)

BTest_shot = tk.Button(controllerWindow, text="Test Shot", command=testShot, background="white")
BTest_shot.place(x=140, y=420)

BGridToggle = tk.Button(controllerWindow, text="Toggle Grid", command=gridToggle)
BGridToggle.place(x=210, y=420)

BRecord = tk.Button(controllerWindow, text="Record On", command=recordFire)
BRecord.place(x=300, y=420)


label = tk.Label(controllerWindow, text="Valve Open Time 5ms", fg="red", anchor="ne")
label.pack(fill="both")

sliderThresUpp= tk.Scale(controllerWindow, from_=0, to=50000, orient="horizontal", label="Detected Area Upper Thres", length=5000, tickinterval=10,
                       resolution=10)
sliderThresUpp.place(x=420, y=20, width=250, height=60)
sliderThresUpp.set(sliderThresUppDefault)

sliderThresLow= tk.Scale(controllerWindow, from_=0, to=10000, orient="horizontal", label="Detected Area Lower Thres", length=5000, tickinterval=10,
                       resolution=10)
sliderThresLow.place(x=420, y=90, width=250, height=60)
sliderThresLow.set(sliderThresLowDefault)

sliderWidth= tk.Scale(controllerWindow, from_=0, to=camWidth, orient="horizontal", label="Row Size", length=5000, tickinterval=10,
                       resolution=0)
sliderWidth.place(x=420, y=160, width=250, height=60)
sliderWidth.set(sliderWidthDefault)

sliderCentre= tk.Scale(controllerWindow, from_=-camWidth/2, to=camWidth/2, orient="horizontal", label="Spray centre offset", length=5000, tickinterval=1,
                       resolution=0)
sliderCentre.place(x=420, y=230, width=250, height=60)
sliderCentre.set(sliderCentreDefault)

sliderDelay= tk.Scale(controllerWindow, from_=-50, to=50, orient="horizontal", label="Fire Delay", length=1000, tickinterval=1,
                       resolution=1)
sliderDelay.place(x=420, y=300, width=250, height=60)
sliderDelay.set(slideDelayDefault)

sliderVOffset= tk.Scale(controllerWindow, from_=-0.2, to=0.2, orient="horizontal", label="Velocity Offset", length=1000, tickinterval=0.001,
                       resolution=0.001)
sliderVOffset.place(x=420, y=370, width=250, height=60)
sliderVOffset.set(slideVOffsetDefault)

sliderPixOffset= tk.Scale(controllerWindow, from_=-100, to=100, orient="horizontal", label="Pix2meter Offset", length=1000, tickinterval=1,
                       resolution=1)
sliderPixOffset.place(x=420, y=440, width=250, height=60)
sliderPixOffset.set(sliderPixDefault)

sliderFPS=tk.Scale(controllerWindow, from_=0, to=15, orient="horizontal", label="Frame Rate", length=1000, tickinterval=1,
                       resolution=0.5)
sliderFPS.place(x=420, y=510, width=250, height=60)
sliderFPS.set(sliderFPSDefault)

videoWindow.protocol("WM_DELETE_WINDOW", donothing)
videoWindow.bind("<Button-1>", getMouseClickPosition)



if __name__ == "__main__":
    plc_res = client.connect() #checks if PLC is connected
    if plc_res:
        print("Connected to PLC")
        setValveTime(valveTime) # sets initial valve open time. Also hard coded into PLC
    else: 
        print("Failed to connect to PLC")
    
    q = multiprocessing.Queue() # Queue to pass firing times between processes
    p1 = multiprocessing.Process(target=multiProcessFireCheck,args = (q,)) # seperate process where fire checking in performed
    p1.start() # starts process

    #initialises Lucid camera
    devices = create_devices_with_tries()
    nodemap = devices.nodemap
    nodes = nodemap.get_node(['ExposureAuto', 'ExposureTime', 'GainAuto', 'Gain', 'Width', 'OffsetX', 'Gamma',
                            'TriggerSelector', 'TriggerMode','TriggerSource','LineSelector','LineMode', 'LineSource', 'LineInverter'])
    nodes['ExposureAuto'].value = 'Off'
    nodes['ExposureTime'].value = exposure_time
    nodes['GainAuto'].value = 'Off'
    nodes['Gain'].value = gain_db
    nodes['Gamma'].value = 0.45
    nodes['TriggerSelector'].value = 'FrameStart'
    nodes['TriggerMode'].value = 'On'
    nodes['TriggerSource'].value = 'Software'
    nodes['LineSelector'].value = 'Line3'
    nodes['LineMode'].value = 'Output'  
    nodes['LineInverter'].value = True
    #print("width",nodes['Width'].value)
    
    nodes['Width'].value =  cropSize
    nodes['OffsetX'].value = int((4096-cropSize)/2)+200
    if flash:
        nodes['LineSource'].value = 'ExposureActive' 
    else:
        nodes['LineSource'].value = 'Off'
    devices.tl_stream_nodemap.get_node('StreamBufferHandlingMode').value = 'NewestOnly'
    devices.tl_stream_nodemap.get_node('StreamPacketResendEnable').value = True
    devices.tl_stream_nodemap.get_node('StreamAutoNegotiatePacketSize').value = True
    devices.nodemap.get_node('PixelFormat').value = "BayerRG8" 
    devices.start_stream()

    #begins main program
    main()
    tk.mainloop()






