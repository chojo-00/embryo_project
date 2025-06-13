from evenness import get_evenness_grade
from predict_embryo import predict_fragmentation_grade
import os
import json
import subprocess
import numpy as np
from PIL import Image
from shutil import copyfile
import requests
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

import shutil

ranking_list = []  # 순위 저장용

# 서버 시작 시 특정 폴더 안의 내용만 모두 삭제
for folder in ["data", "result", "test"]:
    folder_path = os.path.join(os.getcwd(), folder)
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)  # 파일 또는 링크 삭제
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # 하위 폴더 삭제
            except Exception as e:
                print(f"[오류] {file_path} 삭제 실패:", e)

# Gemini API 키
GEMINI_API_KEY = "AIzaSyB5Qubo64ZY_Nf_eGWZ7Z-jIcoWhvvwJhc"

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "data"
VECTOR_STORE_PATH = "faiss_index"
EMBRYO_UPLOAD_FOLDER = "test"
RESULT_FOLDER = "result"

# 폴더 생성
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EMBRYO_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# PDF 임베딩 처리
def load_and_embed_documents():
    documents = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.endswith(".pdf"):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            reader = PdfReader(filepath)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.create_documents([text], metadatas=[{"source": filename}])
            documents.extend(splits)

    if documents:
        vectorstore = FAISS.from_documents(documents, embedding)
        vectorstore.save_local(VECTOR_STORE_PATH)

@app.on_event("startup")
def on_startup():
    load_and_embed_documents()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_location, "wb") as f:
        f.write(await file.read())
    load_and_embed_documents()
    return {"filename": file.filename}

@app.post("/ask")
async def ask(request: Request):
    data = await request.json()
    question = data.get("question")

    if not question or question.strip() == "":
        return JSONResponse(content={"answer": "질문을 입력해주세요.", "sources": []})

    vectorstore = FAISS.load_local(
        VECTOR_STORE_PATH,
        embedding,
        allow_dangerous_deserialization=True
    )
    docs = vectorstore.similarity_search(question, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    source_name = docs[0].metadata.get("source", "분석 결과").replace(".pdf", "")
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            f"[주의] 아래 분석 결과는 PDF 파일 이름이 '{source_name}'인 배아에 대한 것입니다. 답변에 반드시 이 파일명을 포함하세요.\n\n"
                            "너는 산부인과에서 근무하는 배아 분석 전문가야. 사용자는 방금 분석된 배아 결과를 요청했어.\n"
                            "- 세포 수가 8개 이상이면 양호함을 의미해.\n"
                            "- 균등도(Evenness)는 1~4등급: 1등급은 균형이 좋고, 2~3등급은 사용 가능, 4등급은 비추천이야.\n"
                            "- 파편화(Fragmentation)도 1~4등급으로 1등급이 가장 양호해.\n"
                            "설명은 간결하고 전문가처럼 말해줘. 등급만 나열하지 말고, 이식 가능성에 대한 해석도 포함해줘.\n"
                            "마크다운은 사용하지 마.\n\n"
                            f"[PDF 파일 이름]: {source_name}\n"
                            f"[질문]: {question}\n\n"
                            f"[문서 요약]:\n{context}\n\n"
                            "위 분석 내용을 바탕으로 해석해줘. 파일명을 포함한 전문적인 보고 방식으로 작성해."
                        )
                    }
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    try:
        answer = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        answer = "답변 생성에 실패했습니다. 다시 시도해주세요."

    sources = list({doc.metadata.get("source", "알 수 없음") for doc in docs})
    return JSONResponse(content={"answer": answer, "sources": sources})

# Embryo 이미지 업로드 → test 폴더에 저장
@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    filename = file.filename
    path = os.path.join(EMBRYO_UPLOAD_FOLDER, filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    return {"success": True, "filename": filename}

# 모델 실행 → concat 이미지 + 세포 수 반환
@app.post("/run-model")
async def run_model():
    try:
        subprocess.run(["python", "run_cellpose_and_organize.py"], check=True)

        latest_folder = sorted(os.listdir(RESULT_FOLDER))[-1]
        folder_path = os.path.join(RESULT_FOLDER, latest_folder)

        seg_file = [f for f in os.listdir(folder_path) if f.endswith("_seg.npy")][0]
        seg_path = os.path.join(folder_path, seg_file)
        base_name = seg_file.split("_seg.npy")[0]
        original_image = base_name + ".png"

        # static에 이미지 복사
        copyfile(os.path.join(folder_path, base_name + "_colored_mask.png"), os.path.join("static", base_name + "_colored_mask.png"))
        copyfile(os.path.join(folder_path, base_name + "_overlay.png"), os.path.join("static", base_name + "_overlay.png"))
        copyfile(os.path.join("test", original_image), os.path.join("static", original_image))

        # 마스크 로딩
        data = np.load(seg_path, allow_pickle=True)
        if isinstance(data, dict) or hasattr(data, 'item'):
            data = data.item() if hasattr(data, 'item') else data
            mask = data["masks"]
        else:
            mask = data

        cell_count = int(np.max(mask))
        evenness_grade = get_evenness_grade(seg_path)
        image_path = os.path.join("test", original_image)  # 업로드된 원본 경로
        fragmentation_grade = predict_fragmentation_grade(image_path)
        
       # PDF 생성 및 저장
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()

        # ✅ 폰트 파일 경로
        font_path = os.path.join("fonts", "NanumGothic.ttf")

        try:
            if not os.path.exists(font_path):
                raise FileNotFoundError("폰트 파일이 존재하지 않음")

            pdf.add_font("Nanum", "", font_path, uni=True)  # 한글 가능하게
            pdf.set_font("Nanum", size=14)
        except Exception as e:
            print("[⚠️ 폰트 오류] 기본 폰트로 대체됨:", e)
            pdf.set_font("Arial", size=14)

        # 텍스트 출력
        pdf.cell(200, 10, txt=f"Cell: {cell_count}", ln=True)
        pdf.cell(200, 10, txt=f"Evenness: {evenness_grade}", ln=True)
        pdf.cell(200, 10, txt=f"Fragmentation: {fragmentation_grade}", ln=True)

        # 저장
        pdf_filename = base_name + ".pdf"
        pdf_output_path = os.path.join("data", pdf_filename)
        pdf.output(pdf_output_path)

        # 챗봇 업로드
        load_and_embed_documents()

        if 7 <= cell_count <= 10:
            even_score = {"1등급": 3, "2등급": 2, "3등급": 1, "4등급": 0}.get(evenness_grade, 0)
            frag_score = {"1등급": 3, "2등급": 2, "3등급": 1, "4등급": 0}.get(fragmentation_grade, 0)
            total_score = even_score + frag_score
            ranking_list.append({
                "filename": original_image,
                "cell": cell_count,
                "evenness": evenness_grade,
                "fragmentation": fragmentation_grade,
                "score": total_score
            })
        sorted_rank = sorted(ranking_list, key=lambda x: x["score"], reverse=True)
        top3 = sorted_rank[:3]
        
        print("Evenness 등급:", evenness_grade)
        print("Fragmentation 등급:", fragmentation_grade)

        return {
            "success": True,
            "filename": original_image,
            "cell_count": cell_count,
            "evenness": evenness_grade,
            "fragmentation": fragmentation_grade,
            "ranking": top3
        }
    

    except Exception as e:
        return {"success": False, "message": str(e)}

import os

@app.post("/reset-folders")
def reset_folders():
    try:
        for folder in ["data", "result", "test"]:
            folder_path = os.path.join(os.getcwd(), folder)  # 현재 경로 기준
            if os.path.exists(folder_path):
                for item in os.listdir(folder_path):
                    item_path = os.path.join(folder_path, item)
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
        ranking_list.clear()
                        
        return {"success": True}
    except Exception as e:
        return {"success": False, "message": str(e)}





