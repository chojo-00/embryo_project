//초기화 버튼
async function resetServer() {
  const confirmReset = confirm("정말로 모든 결과를 초기화하시겠습니까?");
  if (!confirmReset) return;

  const res = await fetch("/reset-folders", { method: "POST" });
  const data = await res.json();

  if (data.success) {
    alert("초기화 완료되었습니다.");
    window.location.reload(); // 새로고침하여 UI 리셋
  } else {
    alert("초기화 실패: " + data.message);
  }
}

// 모든 DOM이 로드된 후 실행되도록 보장
document.addEventListener("DOMContentLoaded", () => {

  // 이미지 업로드
  async function handleImageUpload() {
    const fileInput = document.getElementById("image-upload");
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/upload-image", {
      method: "POST",
      body: formData
    });

    const data = await res.json();
    alert(data.success ? "이미지 업로드 완료!" : "업로드 실패");
  }

  // 모델 실행
  async function runModel() {
    const res = await fetch("/run-model", { method: "POST" });
    const data = await res.json();

    /* --- 순위 갱신 --- */
    if (data.ranking && data.ranking.length > 0) {
      const box = document.getElementById("ranking-box");
      const lines = data.ranking.map((item, index) => {
        const medal = ["🥇", "🥈", "🥉"][index] || "";
        return `${medal} ${index + 1}위: ${item.filename} (${item.evenness}, ${item.fragmentation})`;
      });
      box.innerHTML = lines.join("<br>");
    }

    /* --- 결과 반영 --- */
    if (data.success) {
      const baseName = data.filename.split(".")[0];

      const original = document.getElementById("original-image");
      const mask     = document.getElementById("mask-image");
      const overlay  = document.getElementById("overlay-image");
      if (!original || !mask || !overlay) {
        alert("이미지 프리뷰 요소를 찾을 수 없습니다.");
        return;
      }
      original.src = "/static/" + data.filename;
      mask.src     = "/static/" + baseName + "_colored_mask.png";
      overlay.src  = "/static/" + baseName + "_overlay.png";

      const cell      = document.getElementById("preg-score");
      const evenness  = document.getElementById("grade");
      const fragSpan  = document.getElementById("circularity");
      if (cell)     cell.textContent = data.cell_count;
      if (evenness) evenness.textContent = data.evenness || "N/A";
      if (fragSpan) fragSpan.textContent = data.fragmentation || "";
    } else {
      alert("모델 실행 실패: " + data.message);
    }
  }

  window.handleImageUpload = handleImageUpload;
  window.runModel          = runModel;
});

/* ------------------- 공통 함수 ------------------- */
function updateRanking(top) {
  const ranks = [
    "🥇 1위: Embryo 1 (4AA)",
    "🥈 2위: Embryo 2 (4AA)",
    "🥉 3위: Embryo 3 (4CB)"
  ];
  document.getElementById("ranking-box").innerHTML =
    ranks.slice(0, top).join("<br>");
}

/* ------------------- 파편화 ------------------- */
function showFragmentImage(index, btn) {
  const img = document.getElementById("sim-img");
  img.src = `/static/f${index}.png`;

  document
    .querySelectorAll("#fragment-section .sim-btn")
    .forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  const fragmentDescriptions = [
    "1단계 -> 파편이 거의 없고, 착상에 영향이 없습니다.",
    "2단계 -> 소량의 파편이 있으나 정상 발달에 큰 문제는 없습니다.",
    "3단계 -> 중등도 파편이 존재해 착상률에 일부 영향을 줄 수 있습니다.",
    "4단계 -> 파편이 많아 착상과 발달에 부정적인 영향을 미칩니다."
  ];
  const descElem = document.getElementById("fragment-description");
  if (descElem) {
    descElem.textContent = fragmentDescriptions[index - 1];
    descElem.style.display = "block";
  }
}

/* ------------------- 원형도 ------------------- */
function showRoundnessImage(index, btn) {
  const image = document.getElementById("roundness-display");
  image.src = `/static/r${index}.png`;

  document
    .querySelectorAll("#roundness-section .sim-btn")
    .forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  const roundnessDescriptions = [
    "1단계 -> 세포 크기가 매우 고르고, 전반적으로 건강한 상태입니다.",
    "2단계 -> 대부분 균등하나 약간의 크기 차이가 있습니다.",
    "3단계 -> 크기 차이가 명확히 보이고 균형이 다소 무너져 있습니다.",
    "4단계 -> 세포 간 불균형이 뚜렷하고 발달 가능성이 낮아 보입니다."
  ];
  const descElem = document.getElementById("roundness-description");
  if (descElem) {
    descElem.textContent = roundnessDescriptions[index - 1];
    descElem.style.display = "block";
  }
}

/* ------------------- 분석 탭 토글 ------------------- */
function showAnalysis(type) {
  document
    .querySelectorAll(".analysis-btn")
    .forEach(btn => btn.classList.remove("active"));

  if (type === "fragment") {
    document.getElementById("fragment-section").style.display = "block";
    document.getElementById("roundness-section").style.display = "none";
    document.querySelectorAll(".analysis-btn")[0].classList.add("active");
  } else {
    document.getElementById("fragment-section").style.display = "none";
    document.getElementById("roundness-section").style.display = "block";
    document.querySelectorAll(".analysis-btn")[1].classList.add("active");
  }
}

/* ------------------- PDF 업로드 ------------------- */
document
  .getElementById("upload-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    const res = await fetch("/upload-pdf", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    alert(data.message || "PDF 업로드 완료");
  });

/* ------------------- 챗봇 전송 ------------------- */
async function sendMessage() {
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  if (!message) return;

  const chatWindow = document.getElementById("chat-window");

  const userDiv = document.createElement("div");
  userDiv.className = "bubble user";
  userDiv.textContent = "나: " + message;
  chatWindow.appendChild(userDiv);

  const res = await fetch("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: message })
  });
  const data = await res.json();

  const botDiv = document.createElement("div");
  botDiv.className = "bubble bot";
  botDiv.innerHTML = "<strong>Gemini:</strong><br>" + data.answer;
  chatWindow.appendChild(botDiv);

  chatWindow.scrollTop = chatWindow.scrollHeight;
  input.value = "";
}
