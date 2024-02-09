Eaxmple YOLO models that differentiate between dicot crop, dicot weeds, monocot crop and monocot weeds. Note that these are iniital test models and their performance needs improving. They are best used to differentitate between monocots and dicots. 

For optimal inferencing on the Jetson, convert .pt files to .engine TensorRT filesusing the export.py file. Be sure to set imgsz to the required resolution. 

To run files on PC, use the .pt files. 

If you want to test the model is working on your system, use the "simple_predict.py" script. 
