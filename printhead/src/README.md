The main script runs the targeting and valvle firing system utilising the YOLO model with object segmentation. 
The colour_detection script instead uses OpenCV colour detection to identify targets - this is best used for system setup and calibration rather than plant targeting. 

To run the main script on a Jetson, ensure you are using the ".engine" model  for optiium speed. Use the ".pt" model for use with a PC. This is adjusted on line 37. 
