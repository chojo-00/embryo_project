import os
import shutil
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image

# 📂 최신 이미지 자동 탐색
test_dir = "test"
latest_img = sorted(
    [f for f in os.listdir(test_dir) if f.endswith(".png")],
    key=lambda x: os.path.getmtime(os.path.join(test_dir, x)),
    reverse=True
)[0]
image_path = os.path.join(test_dir, latest_img)
image_name = os.path.splitext(latest_img)[0]

# 📁 결과 디렉토리 설정
result_dir = os.path.join("result", image_name)
os.makedirs(result_dir, exist_ok=True)

# 1. Cellpose 실행
print("[🧠] Cellpose 실행 중...")
command = [
    "python", "-m", "cellpose",
    "--image_path", image_path,
    "--use_gpu",
    "--pretrained_model", r"C:/Users/yeong/cellpose/embryo_sam_model",  # ← 여기에 경로 추가
    "--chan", "0", "--chan2", "2",
    "--save_png",
#    "--save_flows",
    "--verbose",
    "--no_resample",
    "--flow_threshold", "0.4",
    "--cellprob_threshold", "-0.5",
    "--exclude_on_edges",
    "--savedir", result_dir
]
subprocess.run(command)

# 2. seg.npy 이동
seg_src = image_path.replace(".png", "_seg.npy")
seg_dst = os.path.join(result_dir, os.path.basename(seg_src))
#seg_dst = os.path.join(result_dir, f"{image_name}_seg.npy")
if os.path.exists(seg_src):
    shutil.move(seg_src, seg_dst)
    print(f"[✅] seg.npy 이동 완료: {seg_dst}")
else:
    print("[⚠️] seg.npy 파일이 존재하지 않음")

# 3. 시각화 생성
print("[🎨] 시각화 생성 중...")

data = np.load(seg_dst, allow_pickle=True)
mask = data.item().get("masks") if isinstance(data, dict) or hasattr(data, 'item') else data

if mask is None or not np.any(mask):
    raise ValueError("유효한 마스크가 존재하지 않습니다.")

n_cells = len(np.unique(mask)) - 1
print("세포 수:", n_cells)

# 컬러 마스크 생성
cmap = plt.get_cmap('tab20', np.max(mask)+1)
norm = mcolors.BoundaryNorm(np.arange(0, np.max(mask)+2)-0.5, cmap.N)
colored_mask = cmap(norm(mask))[..., :3]

# 이미지 저장
colored_path = os.path.join(result_dir, f"{image_name}_colored_mask.png")
Image.fromarray((colored_mask * 255).astype(np.uint8)).save(colored_path)

orig_img = Image.open(image_path).convert("RGB").resize((mask.shape[1], mask.shape[0]))
overlay = (np.array(orig_img) * 0.5 + colored_mask * 255 * 0.5).astype(np.uint8)
overlay_path = os.path.join(result_dir, f"{image_name}_overlay.png")
Image.fromarray(overlay).save(overlay_path)

concat = np.concatenate([
    np.array(orig_img),
    (colored_mask * 255).astype(np.uint8),
    overlay
], axis=1)
concat_path = os.path.join(result_dir, f"{image_name}_concat.png")
Image.fromarray(concat).save(concat_path)

print(f"[✅] 시각화 저장 완료: {result_dir}")
