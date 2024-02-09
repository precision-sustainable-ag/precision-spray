from ultralytics import YOLO


# Change these as you see fit
imgsz = (1344,896)  # 	image size as scalar or (h, w) list, i.e. (640, 480)
keras = False  # 	use Keras for TF SavedModel export
optimize = False  # 	TorchScript: optimize for mobile
half = False  # 	FP16 quantization
int8 = False  # 	INT8 quantization
dynamic = False  # 	ONNX/TensorRT: dynamic axes
simplify = False  # 	ONNX/TensorRT: simplify model
opset = None  # 	ONNX: opset version (optional, defaults to latest)
workspace = 8  # 	TensorRT: workspace size (GB)
nms = False  # 	CoreML: add NMS

# change this to your path
model_path = 'yolov8s_seg_v0.3_scaled_0.3.pt'
# Load a model
#model=YOLO('yolov8n.pt')
model = YOLO(model_path)

# Export the model
model.export(
    format="engine",
    imgsz=imgsz,
    keras=keras,
    optimize=optimize,
    half=half,
    int8=int8,
    dynamic=dynamic,
    simplify=simplify,
    opset=opset,
    workspace=workspace,
    nms=nms,
    verbose = True
    
)
