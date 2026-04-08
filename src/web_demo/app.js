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
const probabilityList = document.querySelector("#probability-list");
const heroJumpButtons = document.querySelectorAll("[data-jump-tab]");

const emotionLabels = {
  angry: "Ofkeli",
  disgust: "Igrenme",
  fear: "Korku",
  happy: "Mutlu",
  sad: "Uzgun",
  surprise: "Sasirmis",
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
  fileName.textContent = file ? file.name : "Heniz dosya secilmedi";
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
  updateSelectedFile(fileInput.files[0]);
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
  if (!file || !file.type.startsWith("image/")) {
    statusPill.textContent = "Gecersiz dosya";
    outputRefs.note.textContent = "Lutfen yalnizca bir gorsel dosyasi surukleyip birak.";
    return;
  }

  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  fileInput.files = dataTransfer.files;
  updateSelectedFile(file);
  statusPill.textContent = "Fotograf hazir";
  outputRefs.note.textContent = "Fotograf alindi. Analiz icin butona basabilirsin.";
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
    probabilityList.innerHTML = "<p class='muted'>Senaryo modunda olasilik dagilimi gosterilmiyor.</p>";
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
    return "Yuksek guven";
  }
  if (score >= 0.55) {
    return "Orta guven";
  }
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
  outputRefs.readinessBadge.textContent =
    plan.confidence >= 0.6 ? "Otomasyon adayi" : "Onay onerilir";
  renderProbabilities(payload.probabilities);
}

async function sendJson(url, payload) {
  statusPill.textContent = "Calisiyor";
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Beklenmeyen bir hata olustu");
  }
  statusPill.textContent = "Hazir";
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
    statusPill.textContent = "Hata";
    outputRefs.note.textContent = error.message;
  }
});

analysisForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = fileInput.files[0];
  if (!file) {
    statusPill.textContent = "Dosya gerekli";
    outputRefs.note.textContent = "Analiz icin once bir gorsel sec.";
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
    statusPill.textContent = "Hata";
    outputRefs.note.textContent = error.message;
  }
});

async function boot() {
  try {
    const response = await fetch("/api/health");
    const health = await response.json();
    statusPill.textContent = health.model_ready ? "Hazir" : "Model yok";
  } catch (error) {
    statusPill.textContent = "Sunucu yok";
  }

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
      summary: "happy duygusu icin enerjik mod onerildi. Ortam: canli ve parlak aydinlatma, muzik: enerjik oynatma listesi.",
    },
    source: "scenario",
    probabilities: {},
    preprocessing_note: "Senaryo modu: el ile secilen duygu kullanildi.",
  };
  renderResult(initialScenario);
}

boot();
