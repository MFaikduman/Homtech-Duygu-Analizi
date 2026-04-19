const tabs = document.querySelectorAll(".tab");
const panes = document.querySelectorAll(".form-pane");
const scenarioForm = document.querySelector("#scenario-form");
const analysisForm = document.querySelector("#analysis-form");
const fileInput = analysisForm.querySelector('input[name="image"]');
const fileDropZone = document.querySelector("#file-drop-zone");
const fileName = document.querySelector("#file-name");
const previewImage = document.querySelector("#preview-image");
const previewPlaceholder = document.querySelector("#preview-placeholder");
const statusPill = document.querySelector("#status-pill");
const statusDetail = document.querySelector("#status-detail");
const probabilityList = document.querySelector("#probability-list");
const heroJumpButtons = document.querySelectorAll("[data-jump-tab]");
const analysisCopy = document.querySelector("#analysis-copy");
const analysisSubmitButton = analysisForm.querySelector('button[type="submit"]');
let predictionAvailable = false;
let predictionLoading = false;
let predictionError = "";
let healthPollTimer = null;

const emotionLabels = {
  angry: "Öfkeli",
  disgust: "İğrenme",
  fear: "Korku",
  happy: "Mutlu",
  sad: "Üzgün",
  surprise: "Şaşırmış",
  neutral: "Nötr",
};

const outputRefs = {
  emotion: document.querySelector("#emotion-output"),
  mode: document.querySelector("#mode-output"),
  automation: document.querySelector("#automation-output"),
  lighting: document.querySelector("#lighting-output"),
  temperature: document.querySelector("#temperature-output"),
  brightness: document.querySelector("#brightness-output"),
  music: document.querySelector("#music-output"),
  privacy: document.querySelector("#privacy-output"),
  source: document.querySelector("#source-output"),
  confidence: document.querySelector("#confidence-output"),
  summary: document.querySelector("#summary-output"),
  note: document.querySelector("#note-output"),
  confidenceBadge: document.querySelector("#confidence-badge"),
  readinessBadge: document.querySelector("#readiness-badge"),
};

function getReadyStatusLabel() {
  if (predictionAvailable) {
    return "Hazır";
  }
  if (predictionLoading) {
    return "Yükleniyor";
  }
  return "Senaryo hazır";
}

function getReadyStatusDetail() {
  if (predictionAvailable) {
    return "Tahmin modeli ve senaryo motoru hazir.";
  }
  if (predictionLoading) {
    return "Tahmin modeli arka planda yükleniyor. Analiz birazdan aktif olacak.";
  }
  return predictionError || "Tahmin modeli yok; senaryo modu kullanılabilir.";
}

function setStatus(text, detail = "") {
  statusPill.textContent = text;
  if (statusDetail) {
    statusDetail.textContent = detail;
  }
}

function setAnalysisAvailability(isAvailable, message) {
  predictionAvailable = isAvailable;
  analysisSubmitButton.disabled = !isAvailable;
  if (analysisCopy) {
    analysisCopy.textContent = message;
  }
}

function isSupportedImage(file) {
  return Boolean(file && file.type.startsWith("image/"));
}

function clearSelectedFile() {
  fileInput.value = "";
  updateSelectedFile(null);
}

function scheduleHealthRefresh(delay = 3000) {
  if (healthPollTimer) {
    clearTimeout(healthPollTimer);
  }

  healthPollTimer = window.setTimeout(() => {
    refreshHealth();
  }, delay);
}

function applyHealth(health) {
  predictionAvailable = Boolean(health.model_ready);
  predictionLoading = Boolean(health.model_loading);
  predictionError = health.model_error || "";

  if (predictionAvailable) {
    setAnalysisAvailability(
      true,
      "Tek kişilik, önde ve iyi ışık alan bir fotoğraf kullanırsan model daha tutarlı sonuç verir.",
    );
  } else if (predictionLoading) {
    setAnalysisAvailability(
      false,
      "Tahmin modeli arka planda yükleniyor. Birazdan analiz butonu aktif olacak.",
    );
    scheduleHealthRefresh();
  } else {
    setAnalysisAvailability(
      false,
      "Tahmin modeli kullanılamıyor. Senaryo modunu kullanmaya devam edebilirsin.",
    );
  }

  setStatus(getReadyStatusLabel(), getReadyStatusDetail());
}

async function refreshHealth() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    applyHealth(health);
  } catch (error) {
    predictionAvailable = false;
    predictionLoading = false;
    predictionError = "";
    setAnalysisAvailability(
      false,
      "Sunucuya bağlanılamadığı için analiz modu geçici olarak kullanılamıyor.",
    );
    setStatus("Sunucu yok", "API şu an erişilebilir değil.");
  }
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((button) => button.classList.remove("active"));
    panes.forEach((pane) => pane.classList.remove("active"));
    tab.classList.add("active");
    document.querySelector(`#${tab.dataset.tab}-form`).classList.add("active");
  });
});

heroJumpButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const targetTab = document.querySelector(`.tab[data-tab="${button.dataset.jumpTab}"]`);
    targetTab?.click();
    targetTab?.scrollIntoView({ behavior: "smooth", block: "center" });
  });
});

document.querySelectorAll('input[type="range"]').forEach((input) => {
  const target = document.querySelector(`[data-range-for="${input.name}"]`);
  input.addEventListener("input", () => {
    target.textContent = Number(input.value).toFixed(2);
  });
});

document.querySelectorAll('.toggle input[type="checkbox"]').forEach((checkbox) => {
  const chip = checkbox.nextElementSibling;
  const sync = () => {
    chip.textContent = checkbox.checked ? "on" : "off";
  };
  checkbox.addEventListener("change", sync);
  sync();
});

function updateSelectedFile(file) {
  fileName.textContent = file ? file.name : "Henüz dosya seçilmedi";
  if (!file) {
    previewImage.hidden = true;
    previewImage.removeAttribute("src");
    previewPlaceholder.hidden = false;
    return;
  }

  const reader = new FileReader();
  reader.onload = () => {
    previewImage.src = reader.result;
    previewImage.hidden = false;
    previewPlaceholder.hidden = true;
  };
  reader.readAsDataURL(file);
}

fileInput.addEventListener("change", () => {
  const [file] = fileInput.files;
  if (file && !isSupportedImage(file)) {
    clearSelectedFile();
    setStatus("Geçersiz dosya", "Yalnızca görsel dosyaları kabul ediliyor.");
    outputRefs.note.textContent = "Lütfen JPG, PNG veya benzeri bir görsel dosyası seç.";
    return;
  }

  updateSelectedFile(file);
  if (file) {
    setStatus(
      predictionAvailable ? "Fotoğraf hazır" : getReadyStatusLabel(),
      predictionAvailable
        ? "Fotoğraf seçildi; analiz isteği gönderilebilir."
        : predictionLoading
          ? "Fotoğraf seçildi. Model yüklenince analiz aktif olacak."
          : "Fotoğraf seçildi ama tahmin modeli şu an hazır değil.",
    );
  }
});

["dragenter", "dragover"].forEach((eventName) => {
  fileDropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    fileDropZone.classList.add("drag-over");
  });
});

["dragleave", "dragend", "drop"].forEach((eventName) => {
  fileDropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    fileDropZone.classList.remove("drag-over");
  });
});

fileDropZone.addEventListener("drop", (event) => {
  const [file] = event.dataTransfer.files;
  if (!isSupportedImage(file)) {
    setStatus("Geçersiz dosya", "Yalnızca görsel dosyaları kabul ediliyor.");
    outputRefs.note.textContent = "Lütfen yalnızca bir görsel dosyası sürükleyip bırak.";
    return;
  }

  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  fileInput.files = dataTransfer.files;
  updateSelectedFile(file);
  setStatus(
    predictionAvailable ? "Fotoğraf hazır" : getReadyStatusLabel(),
    predictionAvailable
      ? "Fotoğraf seçildi; analiz isteği gönderilebilir."
      : predictionLoading
        ? "Fotoğraf seçildi. Model yüklenince analiz aktif olacak."
        : "Fotoğraf seçildi ama tahmin modeli şu an hazır değil.",
  );
  outputRefs.note.textContent = "Fotoğraf alındı. Analiz için butona basabilirsin.";
});

function collectFormState(form) {
  const formData = new FormData(form);
  return {
    time_of_day: formData.get("time_of_day"),
    occupancy: formData.get("occupancy"),
    quiet_hours: formData.get("quiet_hours") === "on",
  };
}

function renderProbabilities(probabilities) {
  probabilityList.innerHTML = "";
  const entries = Object.entries(probabilities || {});
  if (!entries.length) {
    probabilityList.innerHTML = "<p class='muted'>Senaryo modunda olasılık dağılımı gösterilmiyor.</p>";
    return;
  }

  entries
    .sort((a, b) => b[1] - a[1])
    .forEach(([label, score]) => {
      const item = document.createElement("div");
      item.className = "probability-item";
      item.innerHTML = `
        <span>${emotionLabels[label] || label}</span>
        <div class="probability-track">
          <div class="probability-fill" style="width:${(score * 100).toFixed(1)}%"></div>
        </div>
        <strong>${(score * 100).toFixed(1)}%</strong>
      `;
      probabilityList.appendChild(item);
    });
}

function describeConfidence(score) {
  if (score >= 0.75) {
    return "Yüksek güven";
  }
  if (score >= 0.55) {
    return "Orta güven";
  }
  return "Düşük güven";
}

function renderResult(payload) {
  const plan = payload.plan;
  outputRefs.emotion.textContent = emotionLabels[plan.emotion] || plan.emotion;
  outputRefs.mode.textContent = plan.suggested_mode;
  outputRefs.automation.textContent = plan.automation_state;
  outputRefs.lighting.textContent = plan.lighting_scene;
  outputRefs.temperature.textContent = plan.temperature_celsius;
  outputRefs.brightness.textContent = plan.brightness_percent;
  outputRefs.music.textContent = plan.music_scene;
  outputRefs.privacy.textContent = `${plan.blinds_position} / ${plan.notification_policy}`;
  outputRefs.source.textContent = payload.source === "prediction" ? "Model analizi" : "Senaryo modu";
  outputRefs.confidence.textContent = `${plan.confidence.toFixed(2)} güven`;
  outputRefs.summary.textContent = plan.summary;
  outputRefs.note.textContent = payload.preprocessing_note;
  outputRefs.confidenceBadge.textContent = describeConfidence(plan.confidence);
  outputRefs.readinessBadge.textContent =
    plan.confidence >= 0.6 ? "Otomasyon adayı" : "Onay önerilir";
  renderProbabilities(payload.probabilities);
}

async function sendJson(url, payload) {
  setStatus("Çalışıyor", "İstek işleniyor.");
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Beklenmeyen bir hata oluştu");
  }
  setStatus(getReadyStatusLabel(), getReadyStatusDetail());
  return data;
}

scenarioForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(scenarioForm);
  try {
    const result = await sendJson("/api/scenario", {
      emotion: formData.get("emotion"),
      confidence: Number(formData.get("confidence")),
      ...collectFormState(scenarioForm),
    });
    renderResult(result);
  } catch (error) {
    setStatus("Hata", error.message);
    outputRefs.note.textContent = error.message;
  }
});

analysisForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!predictionAvailable) {
    setStatus(
      predictionLoading ? "Yükleniyor" : "Tahmin kapalı",
      predictionLoading
        ? "Tahmin modeli arka planda yükleniyor."
        : "Tahmin modeli şu an kullanılamıyor.",
    );
    outputRefs.note.textContent = predictionLoading
      ? "Model yüklenirken senaryo modunu kullanabilir veya biraz sonra tekrar deneyebilirsin."
      : "Analiz modunu kullanmak için modelin yüklenmiş olması gerekiyor.";
    return;
  }

  const file = fileInput.files[0];
  if (!file) {
    setStatus("Dosya gerekli", "Analiz için bir görsel seçilmedi.");
    outputRefs.note.textContent = "Analiz için önce bir görsel seç.";
    return;
  }

  const base64 = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("Dosya okunurken hata oluştu"));
    reader.readAsDataURL(file);
  });

  const formData = new FormData(analysisForm);
  try {
    const result = await sendJson("/api/predict", {
      image_data: base64,
      use_full_image: formData.get("use_full_image") === "on",
      ...collectFormState(analysisForm),
    });
    renderResult(result);
  } catch (error) {
    setStatus("Hata", error.message);
    outputRefs.note.textContent = error.message;
  }
});

async function boot() {
  setStatus("Kontrol", "Sunucu ve model durumu kontrol ediliyor.");
  await refreshHealth();

  const initialScenario = {
    plan: {
      emotion: "happy",
      confidence: 0.82,
      suggested_mode: "enerjik mod",
      automation_state: "otomatik uygulanabilir",
      lighting_scene: "canlı ve parlak aydınlatma",
      brightness_percent: 75,
      temperature_celsius: 21,
      music_scene: "enerjik oynatma listesi",
      blinds_position: "tam açık",
      notification_policy: "standart bildirim düzeni",
      summary: "happy duygusu için enerjik mod önerildi. Ortam: canlı ve parlak aydınlatma, müzik: enerjik oynatma listesi.",
    },
    source: "scenario",
    probabilities: {},
    preprocessing_note: "Senaryo modu: el ile seçilen duygu kullanıldı.",
  };
  renderResult(initialScenario);
  if (!predictionAvailable) {
    outputRefs.note.textContent = predictionLoading
      ? "Tahmin modeli arka planda yükleniyor; birazdan analiz kullanılabilir olacak."
      : "Tahmin modeli hazır değil; senaryo modu ile devam edebilirsin.";
  }
}

boot();
