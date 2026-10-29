"""Local, explainable visual analysis helpers for StegoVisionAI.
Experimental similarity scores are not identity verification or proof of manipulation.
"""
from io import BytesIO
from PIL import Image, ImageChops, ImageStat, UnidentifiedImageError
import hashlib, math

def load_image(data: bytes):
    if len(data) > 20*1024*1024:
        raise ValueError("Maximum upload size is 20 MB.")
    try:
        im=Image.open(BytesIO(data)); im.verify(); im=Image.open(BytesIO(data)); im.load()
        return im
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValueError("File is not a supported, valid image.")

def image_signature(data: bytes):
    im=load_image(data).convert('RGB').resize((64,64))
    pixels=list(im.getdata())
    # A compact normalized RGB histogram distance; intentionally not a learned embedding.
    hist=[0]*96
    for r,g,b in pixels:
        hist[r//8]+=1; hist[32+g//8]+=1; hist[64+b//8]+=1
    total=sum(hist) or 1
    return [v/total for v in hist]

def similarity(a: bytes,b: bytes):
    ia,ib=load_image(a),load_image(b)
    sa,sb=image_signature(a),image_signature(b)
    # Histogram intersection in [0,1]. It is a coarse visual similarity, not face identity.
    score=sum(min(x,y) for x,y in zip(sa,sb))
    return {"score":round(score*100,2),"method":"normalized RGB histogram intersection","interpretation":"Coarse color-distribution similarity only; not semantic matching or identity verification.","image_a":{"format":ia.format or 'Unknown','width':ia.width,'height':ia.height,"bytes":len(a),"sha256":hashlib.sha256(a).hexdigest()},"image_b":{"format":ib.format or 'Unknown','width':ib.width,'height':ib.height,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}}

def compare_images(a: bytes,b: bytes):
    ia,ib=load_image(a),load_image(b)
    a_info={"format":ia.format or 'Unknown',"width":ia.width,"height":ia.height,"mode":ia.mode,"bytes":len(a),"sha256":hashlib.sha256(a).hexdigest()}
    b_info={"format":ib.format or 'Unknown',"width":ib.width,"height":ib.height,"mode":ib.mode,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
    same_bytes=a_info['sha256']==b_info['sha256']
    same_dimensions=ia.size==ib.size
    result={"identical_files":same_bytes,"same_dimensions":same_dimensions,"image_a":a_info,"image_b":b_info,"differences":[],"limitations":["Pixel differences may result from resizing, recompression, color conversion, or normal editing.","Differences alone do not establish tampering or hidden data."]}
    if not same_dimensions:
        result['differences'].append("Image dimensions differ.")
    if a_info['format']!=b_info['format']:
        result['differences'].append("Image formats differ.")
    if not same_bytes and same_dimensions:
        aa=ia.convert('RGB'); bb=ib.convert('RGB')
        diff=ImageChops.difference(aa,bb)
        stat=ImageStat.Stat(diff)
        result['mean_absolute_channel_difference']=round(sum(stat.mean)/3,4)
        result['changed_pixel_fraction_estimate']=round(sum(1 for px in diff.resize((min(256, diff.width),min(256,diff.height))).getdata() if sum(px)>0)/max(1,diff.resize((min(256,diff.width),min(256,diff.height))).width*diff.resize((min(256,diff.width),min(256,diff.height))).height),4)
        result['differences'].append("Pixel-level differences were measured after RGB conversion.")
    if same_bytes: result['differences'].append("SHA-256 hashes match: files are byte-for-byte identical.")
    elif not result['differences']: result['differences'].append("Files differ at the byte level; no pixel-level comparison was possible.")
    result['visual_similarity']=similarity(a,b)['score']
    return result

def detect_faces(data: bytes):
    """Optional OpenCV Haar face detector; never returns a person's identity."""
    try:
        import cv2, numpy as np
    except ImportError:
        raise RuntimeError("Face detection is an optional feature. Install it with: pip install opencv-python-headless")
    im=load_image(data).convert('RGB')
    arr=np.array(im)[:,:,::-1].copy()
    gray=cv2.cvtColor(arr,cv2.COLOR_BGR2GRAY)
    cascade_path=cv2.data.haarcascades+'haarcascade_frontalface_default.xml'
    cascade=cv2.CascadeClassifier(cascade_path)
    if cascade.empty(): raise RuntimeError("OpenCV face detector could not be loaded.")
    faces=cascade.detectMultiScale(gray,scaleFactor=1.1,minNeighbors=5,minSize=(30,30))
    return {"detector":"OpenCV Haar cascade","face_count":len(faces),"faces":[{"x":int(x),"y":int(y),"width":int(w),"height":int(h)} for x,y,w,h in faces],"limitations":["Detection does not identify a person.","This classical detector can miss faces or detect false positives.","Use only images and camera streams you are authorized to analyze."]}
