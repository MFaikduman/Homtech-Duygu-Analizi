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
const warmupButton = document.querySelector("#warmup-button");
let predictionAvailable = false;
let predictionLoading = false;
let predictionError = "";
let healthPollTimer = null;
let warmupRequested = false;

const emotionLabels = {
  angry: "Ofkeli",
  disgust: "Igrenme",
  fear: "Korku",
  happy: "Mutlu",
  sad: "Uzgün",
  surprise: "Saskin",
  neutral: "Notr",
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
  if (predictionAvailable) return "Hazir";
  if (predictionLoading) return "Yukleniyor";
  return "Senaryo hazir";
}

function getReadyStatusDetail() {
  if (predictionAvailable) return "Analiz ve senaryo kullanima hazir.";
  if (predictionLoading) return "Model arka planda yukleniyor. Birazdan analiz acilacak.";
  return predictionError || "Hizli baslangic icin analiz modeli henuz yuklenmedi.";
}

function setStatus(text, detail = "") {
  statusPill.textContent = text;
  statusDetail.textContent = detail;
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

function scheduleHealthRefresh(delay = 2500) {
  if (healthPollTimer) clearTimeout(healthPollTimer);
  healthPollTimer = window.setTimeout(() => refreshHealth(), delay);
}

function applyHealth(health) {
  predictionAvailable = Boolean(health.model_ready);
  predictionLoading = Boolean(health.model_loading);
  predictionError = health.model_error || "";

  if (predictionAvailable) {
    setAnalysisAvailability(true, "Fotografi secip dogrudan analiz edebilirsin.");
    warmupButton.disabled = true;
    warmupButton.textContent = "Model hazir";
  } else if (predictionLoading) {
    setAnalysisAvailability(false, "Model yukleniyor. Bu sirada senaryo modunu kullanabilirsin.");
    warmupButton.disabled = true;
    warmupButton.textContent = "Hazirlaniyor";
    scheduleHealthRefresh();
  } else {
    setAnalysisAvailability(false, "Analiz icin once modeli hazirla. Baslangici hizlandirmak icin otomatik acilmiyor.");
    warmupButton.disabled = false;
    warmupButton.textContent = "Modeli Hazirla";
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
    warmupButton.disabled = true;
    setAnalysisAvailability(false, "Sunucuya baglanilamadigi icin analiz gecici olarak kapali.");
    setStatus("Sunucu yok", "API erisilebilir degil.");
  }
}

async function requestWarmup() {
  if (predictionAvailable || predictionLoading) return;
  warmupRequested = true;
  warmupButton.disabled = true;
  warmupButton.textContent = "Hazirlaniyor";
  setStatus("Yukleniyor", "Analiz modeli arka planda baslatiliyor.");

  try {
    const response = await fetch("/api/warmup-model", { method: "POST" });
    const data = await response.json();
    applyHealth(data);
  } catch (error) {
    warmupButton.disabled = false;
    warmupButton.textContent = "Modeli Hazirla";
    setStatus("Hata", "Model baslatilamadi.");
  }
}

function setActiveTab(tabName) {
  tabs.forEach((button) => button.classList.toggle("active", button.dataset.tab === tabName));
  panes.forEach((pane) => pane.classList.toggle("active", pane.id === `${tabName}-form`));

  if (tabName === "analysis" && !warmupRequested && !predictionAvailable && !predictionLoading) {
    requestWarmup();
  }
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => setActiveTab(tab.dataset.tab));
});

heroJumpButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setActiveTab(button.dataset.jumpTab);
    document.querySelector(`#${button.dataset.jumpTab}-form`)?.scrollIntoView({ behavior: "smooth", block: "center" });
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
  fileName.textContent = file ? file.name : "Dosya secilmedi";
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
    setStatus("Gecersiz dosya", "Yalnizca gorsel dosyalari kabul ediliyor.");
    outputRefs.note.textContent = "Lutfen JPG veya PNG gibi bir gorsel sec.";
    return;
  }

  updateSelectedFile(file);
  if (file) {
    setStatus(
      predictionAvailable ? "Fotograf hazir" : getReadyStatusLabel(),
      predictionAvailable ? "Fotograf secildi. Analiz baslatilabilir." : getReadyStatusDetail(),
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
    setStatus("Gecersiz dosya", "Yalnizca gorsel dosyalari kabul ediliyor.");
    outputRefs.note.textContent = "Lutfen tek bir gorsel dosyasi birak.";
    return;
  }

  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  fileInput.files = dataTransfer.files;
  updateSelectedFile(file);
  outputRefs.note.textContent = "Fotograf alindi. Analiz icin butona bas.";
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
  const entries = Object.entries(probabilities || {}).sort((a, b) => b[1] - a[1]).slice(0, 4);

  if (!entries.length) {
    probabilityList.innerHTML = "<p class='muted'>Senaryo modunda olasilik gosterilmiyor.</p>";
    return;
  }

  entries.forEach(([label, score]) => {
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
  if (score >= 0.75) return "Yuksek guven";
  if (score >= 0.55) return "Orta guven";
  return "Dusuk guven";
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
  outputRefs.confidence.textContent = `${plan.confidence.toFixed(2)} guven`;
  outputRefs.summary.textContent = plan.summary;
  outputRefs.note.textContent = payload.preprocessing_note;
  outputRefs.confidenceBadge.textContent = describeConfidence(plan.confidence);
  outputRefs.readinessBadge.textContent = plan.confidence >= 0.6 ? "Uygulanabilir" : "Onay oner";
  renderProbabilities(payload.probabilities);
}

async function sendJson(url, payload) {
  setStatus("Calisiyor", "Istek isleniyor.");
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Beklenmeyen hata olustu");
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
    if (!predictionLoading) {
      await requestWarmup();
    }
    outputRefs.note.textContent = predictionLoading
      ? "Model yuklenirken biraz bekleyip tekrar deneyebilirsin."
      : "Analiz icin modelin hazir olmasi gerekiyor.";
    return;
  }

  const file = fileInput.files[0];
  if (!file) {
    setStatus("Dosya gerekli", "Analiz icin bir gorsel sec.");
    outputRefs.note.textContent = "Analizden once bir fotograf sec.";
    return;
  }

  const base64 = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("Dosya okunurken hata olustu"));
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

warmupButton.addEventListener("click", () => {
  requestWarmup();
});

async function boot() {
  setStatus("Kontrol", "Sunucu durumu kontrol ediliyor.");
  await refreshHealth();

  const initialScenario = {
    plan: {
      emotion: "happy",
      confidence: 0.82,
      suggested_mode: "enerjik mod",
      automation_state: "otomatik uygulanabilir",
      lighting_scene: "canli ve parlak aydinlatma",
      brightness_percent: 75,
      temperature_celsius: 21,
      music_scene: "enerjik oynatma listesi",
      blinds_position: "tam acik",
      notification_policy: "standart bildirim duzeni",
      summary: "happy duygusu icin enerjik mod onerildi.",
    },
    source: "scenario",
    probabilities: {},
    preprocessing_note: "Senaryo modu: el ile secilen duygu kullanildi.",
  };
  renderResult(initialScenario);
}

boot();
