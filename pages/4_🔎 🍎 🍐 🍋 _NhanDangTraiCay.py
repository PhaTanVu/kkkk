import streamlit as st
import numpy as np
import cv2

import sys
import os
import tensorflow as tf
from object_detection.utils import config_util
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder

import base64
@st.cache_data
def get_img_as_base64(file):
    with open(file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

img = get_img_as_base64("image.jpg")

page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] > .main {{
background-image: url("https://images.unsplash.com/photo-1501426026826-31c667bdf23d");
background-size: 200%;
background-position: 30% 45%;
background-repeat: no-repeat;
background-attachment: local;
}}
[data-testid="stSidebar"] > div:first-child {{
background-image: url("data:image/png;base64,{img}");
background-position: 50% 45%;
background-size: 400%;
}}
[data-testid="stSidebarNav"] span {{
color:white;
}}
[data-testid="stHeader"] {{
background: rgba(0,0,0,0);
}}
[data-testid="stToolbar"] {{
right: 2rem;
}}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True
)

if 'load_model' not in st.session_state:
    st.session_state.load_model = True
    st.session_state.configs = config_util.get_configs_from_pipeline_file('pipeline.config')
    st.session_state.detection_model = model_builder.build(model_config=st.session_state.configs['model'], is_training=False)

    # Restore checkpoint
    st.session_state.ckpt = tf.compat.v2.train.Checkpoint(model=st.session_state.detection_model)
    st.session_state.ckpt.restore(os.path.join('ckpt-6')).expect_partial()
    
    st.session_state.category_index = label_map_util.create_category_index_from_labelmap('label_map.pbtxt')

config = tf.compat.v1.ConfigProto(gpu_options = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.8)
#device_count = {'GPU': 1}
)
config.gpu_options.allow_growth = True
session = tf.compat.v1.Session(config=config)
tf.compat.v1.keras.backend.set_session(session)

#print("Tran Tien Duc - Num GPUs Available: ", len(tf.config.list_physical_devices('GPU')))

@tf.function
def detect_fn(image):
    image, shapes = st.session_state.detection_model.preprocess(image)
    prediction_dict = st.session_state.detection_model.predict(image, shapes)
    detections = st.session_state.detection_model.postprocess(prediction_dict, shapes)
    return detections


def XoaTrung(a, L):
    index = []
    flag = np.zeros(L, np.bool_)
    for i in range(0, L):
        if flag[i] == False:
            flag[i] = True
            x1 = (a[i,0] + a[i,2])/2
            y1 = (a[i,1] + a[i,3])/2
            for j in range(i+1, L):
                x2 = (a[j,0] + a[j,2])/2
                y2 = (a[j,1] + a[j,3])/2
                d = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                if d < 0.2:
                    flag[j] = True
            index.append(i)
    for i in range(0, L):
        if i not in index:
            flag[i] = False
    return flag


st.subheader('Nhận dạng trái cây')

with open("test.zip", "rb") as fp:
    btn = st.download_button(
        label="Download ZIP",
        data=fp,
        file_name="test.zip",
        mime="application/zip"
    )


FRAME_WINDOW = st.image([])

image = cv2.imread('NoImage.bmp', cv2.IMREAD_COLOR)
FRAME_WINDOW.image(image, channels='BGR')

uploaded_file = st.file_uploader("Choose a image file", type="bmp")

if uploaded_file is not None:
    # Convert the file to an opencv image.
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    opencv_image = cv2.imdecode(file_bytes, 1)

    # Now do something with the image! For example, let's display it:
    FRAME_WINDOW.image(opencv_image, channels='BGR')
    press = st.button('Nhận dạng')
    if press:
        image_ket_qua = opencv_image.copy()
        image_np = np.array(image_ket_qua)
        input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
        detections = detect_fn(input_tensor)

        num_detections = int(detections.pop('num_detections'))
        detections = {key: value[0, :num_detections].numpy()
                    for key, value in detections.items()}
        detections['num_detections'] = num_detections

        # detection_classes should be ints.
        detections['detection_classes'] = detections['detection_classes'].astype(np.int64)

        label_id_offset = 1
        image_np_with_detections = image_np.copy()

        my_box = detections['detection_boxes']
        my_class = detections['detection_classes']+label_id_offset
        my_score = detections['detection_scores']

        my_score = my_score[my_score >= 0.7]
        L = len(my_score)
        my_box = my_box[0:L]
        my_class = my_class[0:L]

        flagTrung = XoaTrung(my_box, L)
        my_box = my_box[flagTrung]
        my_class = my_class[flagTrung]
        my_score = my_score[flagTrung]

        # viz_utils.visualize_boxes_and_labels_on_image_array(
        #         image_np_with_detections,
        #         detections['detection_boxes'],
        #         detections['detection_classes']+label_id_offset,
        #         detections['detection_scores'],
        #         category_index,
        #         use_normalized_coordinates=True,
        #         max_boxes_to_draw=5,
        #         min_score_thresh=.5,
        #         agnostic_mode=False)

        viz_utils.visualize_boxes_and_labels_on_image_array(
                image_np_with_detections,
                my_box,
                my_class,
                my_score,
                st.session_state.category_index,
                use_normalized_coordinates=True,
                max_boxes_to_draw=5,
                min_score_thresh=.7,
                agnostic_mode=False)

        FRAME_WINDOW.image(image_np_with_detections, channels='BGR')


