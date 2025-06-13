# embryo\_project

## 프로젝트 개요 (Project Overview)

**embryo\_project**는 배아(embryo) 이미지를 분석하여 등급을 자동으로 판정해주는 대시보드입니다. Cellpose 기반의 세포 분할(Segmentation), OpenCV를 활용한 원형도(Circularity) 분석, DenseNet을 기반으로 한 파편화(Fragmentation) 분류, 결과를 설명해주는 챗봇 기능까지 통합된 AI 분석 시스템입니다.

## 주요 기능 (Features)

- **세포 분할 (Cell Segmentation):** Cellpose 모델을 커스터마이징하여 배아 세포의 경계를 자동으로 구분합니다.
- **원형도 분석 (Circularity Analysis):** OpenCV를 사용하여 각 세포의 형태가 얼마나 원형에 가까운지 수치로 계산합니다.
- **파편화 분류 (Fragmentation Classification):** DenseNet 기반의 분류 모델로 배아의 파편화 정도를 자동 예측합니다.
- **챗봇 기반 결과 설명:** 분석 결과를 사용자가 질문하면, 자연어로 친절히 설명해주는 챗봇 기능이 탑재되어 있습니다.
- **웹 기반 대시보드:** 이미지 업로드 → 분석 → 결과 시각화까지 가능한 직관적인 웹 UI 제공 (Flask 기반)

## 사용 기술 (Technologies Used)

- Python 3
- PyTorch (딥러닝 모델 구현)
- Cellpose (세포 분할)
- OpenCV (이미지 처리 및 원형도 계산)
- DenseNet (파편화 분류용 CNN 모델)
- Flask (웹 대시보드 프레임워크)
- 기타: NumPy, tqdm 등

## 설치 방법 (Installation Instructions)

```bash
# 1. 레포지토리 클론
$ git clone https://github.com/chojo-00/embryo_project.git
$ cd embryo_project

# 2. 가상환경 생성 (선택)
$ python -m venv venv
$ source venv/bin/activate  # 윈도우는 venv\Scripts\activate

# 3. 의존성 설치
$ pip install -r requirements.txt
```

## 실행 방법 (How to Run)

```bash
# Conda 환경 활성화
conda activate cellpose

# 프로젝트 폴더 이동 (예: C 드라이브 바탕화면)
cd C:\Users\Desktop\rag-chatbot

# FastAPI 서버 실행
python -m uvicorn main:app --reload
```

브라우저에서 [http://127.0.0.1:8000](http://127.0.0.1:8000/) 접속 → 이미지 업로드 → 분석 결과 확인 → 챗봇으로 설명 듣기

## 🔗 모델 다운로드 방법 (Model Download Instructions)

GitHub 용량 제한(100MB)을 초과하여 모델 파일은 GitHub에 포함되어 있지 않습니다. 아래 링크를 통해 수동 다운로드 후, `models/` 폴더에 저장하세요:

```markdown
[모델 다운로드 (Dropbox)]([https://www.dropbox.com/s/abc1234/model.pth?dl=1](https://www.dropbox.com/scl/fi/94z2vmzcm7yzsmqfsmcro/embryo_sam_model?rlkey=pntnkarsz8t9lkv4777nnrnaw&st=h5ofslxs&dl=0))
```

- 예: `models/densenet_embryo.pth` 또는 `models/cellpose_custom_model`
- 해당 경로는 코드에서 참조되므로 위치와 파일명이 일치해야 합니다

## 폴더 구조 (Folder Structure)

```
embryo_project/
├── cellpose/                 # 세포 분할 관련 코드 및 모델
├── static/                   # 웹 UI 정적 파일 (CSS, JS 등)
├── templates/                # HTML 템플릿 (Flask)
├── models/                   # (직접 다운로드한) 사전학습 모델 저장 폴더
├── main.py                   # 대시보드 실행 메인 파일
├── predict_embryo.py         # 단일 이미지 분석용 스크립트
├── run_cellpose_and_organize.py  # 세포 분할 실행 스크립트
├── requirements.txt          # 의존성 목록
└── README.md                 # 프로젝트 설명 문서
```


