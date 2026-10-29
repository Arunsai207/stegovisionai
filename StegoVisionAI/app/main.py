from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from pathlib import Path
import json, os
from .database import connect, init_db
from .auth import hash_password, verify_password, create_token, current_user
from .stego import encode_png, decode_png
from .forensics import inspect_image
from .advanced import compare_images, similarity, detect_faces

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="StegoVisionAI", version="2.0.0", description="Steganography, image forensics and visual comparison workspace")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
MAX_UPLOAD = 20 * 1024 * 1024

@app.on_event("startup")
def startup(): init_db()

@app.get("/", response_class=HTMLResponse)
def home(): return (ROOT / "static" / "index.html").read_text(encoding="utf-8")

class RegisterBody(BaseModel): name: str; email: EmailStr; password: str
class LoginBody(BaseModel): email: EmailStr; password: str

@app.post("/api/auth/register")
def register(body: RegisterBody):
    name=body.name.strip(); email=str(body.email).lower().strip()
    if len(name)<2 or len(name)>80: raise HTTPException(400,"Name must be between 2 and 80 characters.")
    if len(body.password)<8: raise HTTPException(400,"Password must contain at least 8 characters.")
    salt,digest=hash_password(body.password)
    try:
        with connect() as con:
            cur=con.execute("INSERT INTO users(name,email,salt,password_hash) VALUES(?,?,?,?)",(name,email,salt,digest)); user_id=cur.lastrowid
    except Exception as e:
        if "UNIQUE" in str(e).upper(): raise HTTPException(409,"An account with this email already exists. Please sign in.")
        raise HTTPException(500,"Could not create account.")
    token=create_token(user_id,email)
    return {"token":token,"user":{"id":user_id,"name":name,"email":email},"welcome":f"Welcome to StegoVisionAI, {name}! Your workspace is ready."}

@app.post("/api/auth/login")
def login(body: LoginBody):
    email=str(body.email).lower().strip()
    with connect() as con: row=con.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
    if not row or not verify_password(body.password,row["salt"],row["password_hash"]): raise HTTPException(401,"Incorrect email or password.")
    return {"token":create_token(row["id"],row["email"]),"user":{"id":row["id"],"name":row["name"],"email":row["email"]},"welcome":f"Welcome back, {row['name']}!"}

@app.get("/api/auth/me")
def me(request: Request):
    payload=current_user(request)
    with connect() as con: row=con.execute("SELECT id,name,email FROM users WHERE id=?",(payload["sub"],)).fetchone()
    if not row: raise HTTPException(401,"Account not found.")
    return {"user":dict(row),"welcome":f"Welcome back, {row['name']}!"}

@app.post("/api/auth/logout")
def logout(): return {"message":"Signed out. Remove the session token on the client."}

async def read_upload(image: UploadFile):
    data=await image.read()
    if not data: raise HTTPException(400,"Uploaded file is empty.")
    if len(data)>MAX_UPLOAD: raise HTTPException(413,"Maximum upload size is 20 MB.")
    return data

@app.post("/api/encode")
async def encode(request: Request,image: UploadFile=File(...),message: str=Form(...),passphrase: str=Form(...)):
    current_user(request); data=await read_upload(image)
    try: result=encode_png(data,message,passphrase)
    except Exception as e: raise HTTPException(400,str(e))
    filename=(image.filename or "image").rsplit(".",1)[0][:100]+"_stegovision.png"
    return Response(result,media_type="image/png",headers={"Content-Disposition":f'attachment; filename="{filename}"'})

@app.post("/api/decode")
async def decode(request: Request,image: UploadFile=File(...),passphrase: str=Form(...)):
    current_user(request); data=await read_upload(image)
    try: message=decode_png(data,passphrase)
    except Exception as e: raise HTTPException(400,str(e))
    return {"message":message}

@app.post("/api/forensics")
async def forensics(request: Request,image: UploadFile=File(...)):
    payload=current_user(request); data=await read_upload(image)
    try: result=inspect_image(image.filename or "upload",data)
    except Exception as e: raise HTTPException(400,str(e))
    save_analysis(payload["sub"],result,"forensics")
    return result

def save_analysis(user_id,result,kind):
    with connect() as con: con.execute("INSERT INTO analyses(user_id,filename,sha256,result_json) VALUES(?,?,?,?)",(user_id,result.get("filename",kind),result.get("sha256",""),json.dumps({"kind":kind,**result})))

@app.post("/api/compare")
async def compare(request: Request,image_a: UploadFile=File(...),image_b: UploadFile=File(...)):
    payload=current_user(request); a=await read_upload(image_a); b=await read_upload(image_b)
    try: result=compare_images(a,b)
    except Exception as e: raise HTTPException(400,str(e))
    result["filename"]=(image_a.filename or "image-a")+" ↔ "+(image_b.filename or "image-b")
    save_analysis(payload["sub"],result,"comparison")
    return result

@app.post("/api/similarity")
async def visual_similarity(request: Request,image_a: UploadFile=File(...),image_b: UploadFile=File(...)):
    current_user(request); a=await read_upload(image_a); b=await read_upload(image_b)
    try: return similarity(a,b)
    except Exception as e: raise HTTPException(400,str(e))

@app.post("/api/faces/detect")
async def faces_detect(request: Request,image: UploadFile=File(...)):
    payload=current_user(request); data=await read_upload(image)
    try: result=detect_faces(data)
    except RuntimeError as e: raise HTTPException(501,str(e))
    except Exception as e: raise HTTPException(400,str(e))
    result["filename"]=image.filename or "upload"
    save_analysis(payload["sub"],result,"face_detection")
    return result

@app.get("/api/analytics")
def analytics(request: Request):
    payload=current_user(request)
    with connect() as con:
        total=con.execute("SELECT COUNT(*) n FROM analyses WHERE user_id=?",(payload["sub"],)).fetchone()["n"]
        rows=con.execute("SELECT result_json,created_at FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT 100",(payload["sub"],)).fetchall()
    kinds={}
    for row in rows:
        try: kind=json.loads(row["result_json"]).get("kind","forensics")
        except Exception: kind="forensics"
        kinds[kind]=kinds.get(kind,0)+1
    return {"total_analyses":total,"recent_count":len(rows),"by_type":kinds,"recent":[{"created_at":r["created_at"]} for r in rows]}

@app.get("/api/history")
def history(request: Request):
    payload=current_user(request)
    with connect() as con: rows=con.execute("SELECT id,filename,sha256,created_at,result_json FROM analyses WHERE user_id=? ORDER BY id DESC LIMIT 100",(payload["sub"],)).fetchall()
    items=[]
    for row in rows:
        try: kind=json.loads(row["result_json"]).get("kind","forensics")
        except Exception: kind="forensics"
        items.append({"id":row["id"],"filename":row["filename"],"sha256":row["sha256"],"created_at":row["created_at"],"kind":kind})
    return {"items":items}

@app.delete("/api/history/{analysis_id}")
def delete_history(analysis_id: int,request: Request):
    payload=current_user(request)
    with connect() as con:
        cur=con.execute("DELETE FROM analyses WHERE id=? AND user_id=?",(analysis_id,payload["sub"]))
        if cur.rowcount==0: raise HTTPException(404,"Record not found.")
    return {"deleted":True,"id":analysis_id}

@app.delete("/api/history")
def clear_history(request: Request):
    payload=current_user(request)
    with connect() as con: cur=con.execute("DELETE FROM analyses WHERE user_id=?",(payload["sub"],))
    return {"deleted_count":cur.rowcount}

@app.get("/api/health")
def health(): return {"status":"ok","app":"StegoVisionAI","version":"2.0.0"}
