from numpy import *
from math import *

"""Calculates and saves the position of the system given a range of input angle"""

R = 1  # radius of top semi circle 

print("running...")

alpha = 0 # angle of the x axis
beta = 0 # angle of the y axis
thetaB = 0 # angle of the base plate
thetaT = 0 # angle of the top motor


file = open("data.txt", "w") #create file 
firstline = "alpha|beta|thetaB|thetaT\n"	# define first line used as a title
file.write(firstline) # write first line in text file

for thetaB in range (0,90*5):
      thetaB = thetaB/5
      thetaBr = radians(thetaB)
      for thetaT in range(0,89*5):
            thetaT = thetaT/5
            thetaTr = radians(thetaT)
            xo = R*cos((pi/2)-thetaTr)
            x = xo*cos(thetaBr)
            z = R*cos(thetaTr)
            y = xo*sin(thetaBr)
            if x == 0:
                alpha = 90
            else:
                alpha = degrees(arctan(z/x))
            if y == 0:
                 beta = 90
            else:
                beta = degrees(arctan(z/y))
            
            if thetaB == 0 :
                 beta = 90
            if thetaT == 0:
                 alpha = 90
                 beta = 90
            if thetaB == 90:
                 alpha = 90
            alpha = abs(alpha)
            beta = abs(beta)
            separator = "|"
            data = str(round(alpha,0)) + separator + str(round(beta,0))+ "#" +str(int(round(thetaB,0)))+ separator + str(int(round(thetaT,0))) + "\n"
            file.write(data)

# for thetaB in range (0,180*5):
#       thetaB = thetaB/5
#       thetaBr = radians(thetaB)
#       for thetaT in range(89*5,-89*5,-1):
#             thetaT = thetaT/5
#             thetaTr = radians(thetaT)
#             xo = R*cos((pi/2)-thetaTr)
#             x = xo*cos(thetaBr)
#             z = R*cos(thetaTr)
#             y = xo*sin(thetaBr)
#             if x == 0:
#                 alpha = 90
#             else:
#                 alpha = degrees(arctan(z/x))
#             if y == 0:
#                  beta = 90
#             else:
#                 beta = degrees(arctan(z/y))
#             if thetaT > 0 and thetaB < 90:
#                  alpha = abs(alpha)
#                  beta = abs(beta)
#             if thetaT < 0 and thetaB < 90:
#                  alpha = 180 - abs(alpha)
#                  beta = -1* abs(beta)
#             if thetaT < 0 and thetaB > 90:
#                  alpha = abs(alpha)
#                  beta = abs(beta)
#             if thetaT > 0 and thetaB > 90:
#                  alpha = 180 - abs(alpha)
#                  beta = -1* abs(beta)
#             if thetaB == 0 :
#                  beta = 90
#             if thetaT == 0:
#                  alpha = 90
#                  beta = 90
#             if thetaB == 90:
#                  alpha = 90
            
#             separator = "|"
#             data = str(round(alpha,0)) + separator + str(round(beta,0))+ "#" +str(int(round(thetaB,0)))+ separator + str(int(round(thetaT,0))) + "\n"
#             file.write(data)


file.close()

print("Terminé")
