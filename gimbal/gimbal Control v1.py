import numpy as np
import time
import tkinter.messagebox
import serial
import serial.tools.list_ports
import math
from math import *

lines = open("data.txt").read().splitlines()  # Read the file data.txt and split it by lines and put it in a list

lines = lines[1:]  # Remove the first line ( because it contains the titles )

dataDict = {}

for i in range(1, len(lines)):  # for loop to go over the lines list and feed it to the dictionary
    key, value = lines[i].split("#")
    alpha, beta = key.split("|")
    thetaB, thetaT = value.split("|")
    dataDict[(float(alpha),float(beta))] = (float(thetaB), float(thetaT))




# def createPointsListCircle():     # create an array of 360 points to describe a whole circle with the argument as radius
#     global pointsListCircle
#     pointsListCircle = []
#     for angle in range(0, 360):
#         angle = angle - 90
#         pointsListCircle.append([sliderRadius.get() * cos(radians(angle)) + 240, sliderRadius.get() * sin(radians(angle)) + 240])



pointsListEight = []        # create an empty list to put points refinates that describes an Eight patern


def createPointsListEight():      # create an array of 360 points to describe an Eight shape with the argument as radius
    global pointsListEight
    radius = 100
    pointsListEight = []
    for angle in range(270, 270 + 360):
        pointsListEight.append([radius * cos(radians(angle)) , radius * sin(radians(angle))  + radius])
    for angle in range(360, 0, -1):
        angle = angle + 90
        pointsListEight.append([radius * cos(radians(angle)) , radius * sin(radians(angle))  - radius])

def shootCartesian(x,y): #points to cartesian coordiantate
    try:
        a,b = motorangle(posToAxisAngle(x),posToAxisAngle(y))
        print(a,b)
        moveGimbal(a,b)
    except:
        print(x,y,'fail')
square = [[100,100],[100,0],[100,-100],[0,-100],[-100,-100],[-100,0],[-100,100],[0,100,],[100,100]]

def drawSqaure(t=0.2):
    for i in range(20):
        for i in range(len(square)):
            shootCartesian(square[i][0]/2,square[i][1]/2) 
            time.sleep(t)
line = []
for x in range(-100,101,50):
    line.append([x,100])
def drawLine(t=0.2):
    for i in range(20):
        for i in range(len(line)):
            shootCartesian(line[i][0],line[i][1]) 
            time.sleep(t)

def donothing():    # function that does nothing, may be used for delay
    pass

def servosTest():   # function that tests the servos by sweeping
    global max_alpha
    if arduinoIsConnected == True:
        if tkinter.messagebox.askokcancel("Warning", "The plate needs to be in Place"):
            for i in range(1):
                alpha = 0
                beta = 0
                while alpha < max_alpha:
                    ser.write((str(dataDict[alpha]+90) + "," + str(dataDict[beta]+90) + "\n").encode())
                    ser.flush()
                    #time.sleep(0.02)
                    alpha = round(alpha + 0.1, 1)
                   # print(str(alpha) + "|" + str(dataDict[alpha]))
                while alpha > -max_alpha:
                    ser.write((str(dataDict[alpha]+90) + "," + str(dataDict[beta]+90) + "\n").encode())
                    ser.flush()
                    #time.sleep(0.02)
                    alpha = round(alpha - 0.1, 1)
                   # print(str(alpha) + "|" + str(dataDict[alpha]))
                while beta < max_alpha:
                    ser.write((str(dataDict[alpha]+90) + "," + str(dataDict[beta]+90) + "\n").encode())
                    ser.flush()
                    #time.sleep(0.02)
                    beta = round(beta + 0.1, 1)
                    #print(str(beta) + "|" + str(dataDict[beta]))
                while beta > -max_alpha:
                    ser.write((str(dataDict[alpha]+90) + "," + str(dataDict[beta]+90) + "\n").encode())
                    ser.flush()
                    #time.sleep(0.02)
                    beta = round(beta - 0.1, 1)
                  #  print(str(beta) + "|" + str(dataDict[beta]))
                while alpha < max_alpha :
                    ser.write((str(dataDict[alpha]+90) + "," + str(dataDict[alpha]+90) + "\n").encode())
                    ser.flush()
                    #time.sleep(0.02)
                    alpha = round(alpha + 0.1, 1)
                   # print(str(alpha) + "|" + str(dataDict[alpha]))
                while alpha > -max_alpha :
                    ser.write((str(dataDict[alpha]+90) + "," + str(dataDict[alpha]+90) + "\n").encode())
                    ser.flush()
                    #time.sleep(0.02)
                    alpha = round(alpha - 0.1, 1)
                   # print(str(alpha) + "|" + str(dataDict[alpha]))
            #time.sleep(5)
            X_adjust = sliderInitialX.get()  # adjust offste angle sent to motor
            Y_adjust = sliderInitialY.get()  # adjust offste angle sent to motor
           # ser.write((str(dataDict[0]) + "," + str(dataDict[0]) + "\n").encode())
            ser.write((str(X_adjust) + "," + str(Y_adjust) + "\n").encode()) #wes
    else:
        if tkinter.messagebox.askokcancel("Warning", "Arduino is not Connected"):
            donothing()


def connectArduino():   # function that checks if arduino is connected or not, initialize the serial and toggles the bools
    global ser
    global label
    global arduinoIsConnected
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        if "Arduino" or "CH340" in p.description:
            print(p)
            ser = serial.Serial(p[0], 19200, timeout=1)
            time.sleep(1)  # give the connection a second to settle
            #label.configure(text="Arduino connecte", fg="#36db8b")
            arduinoIsConnected = True

      
def flipxy(x,y):
    xr = 180 -x
    yr = -y
    return(xr,yr)

def motorangle(a,b):  # angle of base and top motors to achieve x and t angles a and b
    try:
        if a <91 and b < 91:
            mb,mt = dataDict[a,b]
        if a >90 and b >90:
            mb,mt = dataDict[180-a,180-b]
            mt =  -mt
        if a > 90 and b < 91:
            mb,mt = dataDict[180-a,b]
            mb = 180 - mb
        if a < 91 and b > 90:
            mb,mt = dataDict[a,180- b]
            mb = 180 -mb
            mt =  -mt
    
    except:
        print('failed to datadict ', a,b)
    else:
        return(mb,mt)

def moveGimbal(angB,angT):
    ser.write((str(angB*180/270) + "," + str(angT+85) + "\n").encode())
    
def posToAxisAngle(pos, dist = 200): # pos = position on the axis, either x or y. dist = gimbal to paper
    ang = degrees(math.atan(pos/dist)) # angle of the axis to achieve that position
    ang = round(ang,0)
    ang = 90 - ang
    return(ang)

def shootFigEight():
    for i in range(len(pointsListEight)):
        time.sleep(0.1)
        x = pointsListEight[i][0]
        y = pointsListEight[i][1]
        
        try:
            a,b = motorangle(posToAxisAngle(x),posToAxisAngle(y))
            print(a,b)
            moveGimbal(a,b)
        except:
            print(x,y,'fail')


# def flip90(n):
#     rr = -n
#     return(rr)
def main():     # declaring the main function of the program

    
    for theta in range(0,360,5):
        thetaR = radians(theta)
        x = 100*cos(thetaR)
        y = 100*sin(thetaR)
        
        try:
            print(theta, motorangle(posToAxisAngle(x),posToAxisAngle(y)))
            # a,b = dataDict[x,35]
            # print(x,dataDict[x,35], 'flip', flipxy(a,b))
        except:
            print(theta,'fail')
    
    alpha = 45.0
    beta = 45.0


connectArduino()
createPointsListEight()
#shootFigEight()





