# predict_embryo.py

import torch
from torchvision import transforms
from torchvision.models import densenet169
from PIL import Image

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# ✅ 모델 로드
model = densenet169(pretrained=False)
model.classifier = torch.nn.Linear(model.classifier.in_features, 4)
model.load_state_dict(torch.load("densenet169_embryo_masking.pth", map_location=device))
model = model.to(device)
model.eval()

# ✅ 예측 함수 정의
def predict_fragmentation_grade(image_path):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image)
        predicted_class = output.argmax(dim=1).item()

    return f"{predicted_class + 1}등급"
