from ultralytics import YOLO

model_path = "YOLO_models/best_1344x896_v0.2_nano.pt"
img_path = "YOLO_models/test_image.jpg"

model = YOLO(model_path, task='segment')
model.predict(img_path,  save=True,  imgsz = (1344,896) , conf=0.5)

