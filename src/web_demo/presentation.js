const body = document.body;
const slideRefs = Array.from(document.querySelectorAll(".slide"));
const navLinks = Array.from(document.querySelectorAll(".rail-nav a"));
const titleRef = document.querySelector("#project-title");
const subtitleRef = document.querySelector("#project-subtitle");
const goalRef = document.querySelector("#project-goal");
const datasetTotalRef = document.querySelector("#dataset-total");
const currentAccuracyRef = document.querySelector("#current-accuracy");
const reportedAccuracyRef = document.querySelector("#reported-accuracy");
const bestValAccuracyRef = document.querySelector("#best-val-accuracy");
const imageSizeRef = document.querySelector("#image-size");
const heroTagsRef = document.querySelector("#hero-tags");
const spotlightTitleRef = document.querySelector("#spotlight-title");
const spotlightCopyRef = document.querySelector("#spotlight-copy");
const spotlightGridRef = document.querySelector("#spotlight-grid");
const heroSummaryBandRef = document.querySelector("#hero-summary-band");
const datasetSummaryRef = document.querySelector("#dataset-summary");
const splitOverviewRef = document.querySelector("#split-overview");
const datasetBarsRef = document.querySelector("#dataset-bars");
const pipelineStepsRef = document.querySelector("#pipeline-steps");
const techStackRef = document.querySelector("#tech-stack");
const overallMetricsRef = document.querySelector("#overall-metrics");
const f1BarsRef = document.querySelector("#f1-bars");
const matrixImageRef = document.querySelector("#matrix-image");
const trainingCardsRef = document.querySelector("#training-cards");
const resultsSummaryRef = document.querySelector("#results-summary");
const resultsSpotlightRef = document.querySelector("#results-spotlight");
const literatureSummaryRef = document.querySelector("#literature-summary");
const literatureBarsRef = document.querySelector("#literature-bars");
const trainingSummaryRef = document.querySelector("#training-summary");
const highlightGridRef = document.querySelector("#highlight-grid");
const matrixCaptionRef = document.querySelector("#matrix-caption");
const reloadButton = document.querySelector("#reload-data");
const themeToggleButton = document.querySelector("#theme-toggle");
const presentationToggleButton = document.querySelector("#presentation-toggle");
const fullscreenToggleButton = document.querySelector("#fullscreen-toggle");
const slideTitleRef = document.querySelector("#slide-title");
const slideControlsRef = document.querySelector("#slide-controls");
const slideCounterRef = document.querySelector("#slide-counter");
const progressFillRef = document.querySelector("#progress-fill");
const prevSlideButton = document.querySelector("#prev-slide");
const nextSlideButton = document.querySelector("#next-slide");

const slideTitles = {
  hero: "Ozet",
  dataset: "Veri Seti",
  pipeline: "Akis",
  results: "Sonuclar",
  matrix: "Confusion Matrix",
  product: "Urun Fikri",
};

let currentSlideIndex = 0;

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return `%${(Number(value) * 100).toFixed(1)}`;
}

function formatRawPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return `%${Number(value).toFixed(2)}`;
}

function formatNumber(value) {
  return new Intl.NumberFormat("tr-TR").format(Number(value || 0));
}

function renderBars(target, items, maxValue, formatter) {
  target.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "bar-item";
    const width = maxValue > 0 ? (item.value / maxValue) * 100 : 0;
    row.innerHTML = `
      <span>${item.label}</span>
      <div class="bar-track">
        <div class="bar-fill" style="width:${width.toFixed(2)}%"></div>
      </div>
      <strong>${formatter(item.value)}</strong>
    `;
    target.appendChild(row);
  });
}

function renderSplitOverview(dataset) {
  splitOverviewRef.innerHTML = `
    <article class="split-card">
      <span>Train</span>
      <strong>${formatNumber(dataset.train_total)}</strong>
      <p>${dataset.name || "FER-2013"} egitim gorseli</p>
    </article>
    <article class="split-card">
      <span>Test</span>
      <strong>${formatNumber(dataset.test_total)}</strong>
      <p>Model degerlendirme gorseli</p>
    </article>
  `;
}

function renderPipeline(story) {
  pipelineStepsRef.innerHTML = "";
  story.pipeline.forEach((step, index) => {
    const item = document.createElement("article");
    item.className = "timeline-step";
    item.innerHTML = `
      <div class="timeline-index">0${index + 1}</div>
      <p>${step}</p>
    `;
    pipelineStepsRef.appendChild(item);
  });

  techStackRef.innerHTML = "";
  story.tech_stack.forEach((tech) => {
    const chip = document.createElement("span");
    chip.className = "stack-chip";
    chip.textContent = tech;
    techStackRef.appendChild(chip);
  });
}

function renderHeroTags(project, dataset, evaluation) {
  const tags = [
    `${project.emotion_labels.length} duygu sinifi`,
    `${project.image_size.width}x${project.image_size.height} girdi`,
    `${formatNumber(dataset.total_images)} toplam gorsel`,
    `${formatPercent(evaluation.current_report.overall?.accuracy)} artifact accuracy`,
  ];

  heroTagsRef.innerHTML = "";
  tags.forEach((tag) => {
    const chip = document.createElement("span");
    chip.className = "hero-tag";
    chip.textContent = tag;
    heroTagsRef.appendChild(chip);
  });
}

function renderSpotlight(dataset, evaluation) {
  const strongest = evaluation.current_report.strongest_class;
  const weakest = evaluation.current_report.weakest_class;
  const reported = evaluation.reported_best_metrics || {};

  spotlightTitleRef.textContent = "Teknik sonuctan urun hikayesine";
  spotlightCopyRef.textContent =
    "Model ciktisi, akilli ev baglaminda yorumlanabilir kararlar ve kullanici deneyimi ile birlikte ele aliniyor.";

  spotlightGridRef.innerHTML = `
    <article class="spotlight-item">
      <span>En guclu sinif</span>
      <strong>${strongest ? strongest.label : "-"}</strong>
    </article>
    <article class="spotlight-item">
      <span>Gelisim alani</span>
      <strong>${weakest ? weakest.label : "-"}</strong>
    </article>
    <article class="spotlight-item">
      <span>README zirve accuracy</span>
      <strong>${formatPercent(reported.accuracy)}</strong>
    </article>
    <article class="spotlight-item">
      <span>Veri dengesizligi</span>
      <strong>${dataset.dominant_class} / ${dataset.rarest_class}</strong>
    </article>
  `;
}

function renderHeroSummaryBand(dataset, evaluation) {
  heroSummaryBandRef.innerHTML = `
    <article class="summary-band-item">
      <span>Veri kapsami</span>
      <strong>${formatNumber(dataset.train_total)} train / ${formatNumber(dataset.test_total)} test</strong>
      <p>Benchmark veri seti uzerinden egitim ve degerlendirme akisi kuruldu.</p>
    </article>
    <article class="summary-band-item">
      <span>Model sonucu</span>
      <strong>${formatPercent(evaluation.current_report.overall?.accuracy)} accuracy</strong>
      <p>Sinif bazli farkliliklari okumak icin F1 ve confusion matrix ile desteklendi.</p>
    </article>
    <article class="summary-band-item">
      <span>Urun ciktisi</span>
      <strong>Duygudan senaryoya gecis</strong>
      <p>Tahmin edilen ifade, isik, sicaklik, muzik ve bildirim kararlarina baglandi.</p>
    </article>
  `;
}

function renderOverallMetrics(evaluation) {
  const overall = evaluation.current_report.overall || {};
  const weighted = overall.weighted_avg || {};
  const macro = overall.macro_avg || {};
  const reported = evaluation.reported_best_metrics || {};

  overallMetricsRef.innerHTML = `
    <article class="overall-card">
      <span>Accuracy</span>
      <strong>${formatPercent(overall.accuracy)}</strong>
      <p>Artifact classification report sonucu</p>
    </article>
    <article class="overall-card">
      <span>Weighted F1</span>
      <strong>${formatPercent(weighted.f1_score)}</strong>
      <p>Dengesiz siniflara daha uygun genel kalite gostergesi</p>
    </article>
    <article class="overall-card">
      <span>Macro F1</span>
      <strong>${formatPercent(macro.f1_score)}</strong>
      <p>Siniflar arasi daha esit bakis veren ortalama</p>
    </article>
    <article class="overall-card">
      <span>README Zirve</span>
      <strong>${formatPercent(reported.weighted_f1_score)}</strong>
      <p>Raporlanan final weighted F1</p>
    </article>
  `;
}

function renderTrainingCards(evaluation) {
  const training = evaluation.training || {};
  const strongest = evaluation.current_report.strongest_class;
  const weakest = evaluation.current_report.weakest_class;

  trainingCardsRef.innerHTML = `
    <article class="training-card">
      <span>En Iyi Epoch</span>
      <strong>${training.best_epoch || "-"}</strong>
      <p>Val accuracy zirvesi: ${formatPercent(training.best_val_accuracy)}</p>
    </article>
    <article class="training-card">
      <span>Toplam Epoch</span>
      <strong>${training.epochs || "-"}</strong>
      <p>Kayitli egitim gecmisinin toplami</p>
    </article>
    <article class="training-card">
      <span>En Guclu Sinif</span>
      <strong>${strongest ? strongest.label : "-"}</strong>
      <p>${strongest ? `F1: ${formatPercent(strongest.f1_score)}` : "Sinif metrigi bulunamadi."}</p>
    </article>
    <article class="training-card">
      <span>Gelisime Acik Sinif</span>
      <strong>${weakest ? weakest.label : "-"}</strong>
      <p>${weakest ? `F1: ${formatPercent(weakest.f1_score)}` : "Sinif metrigi bulunamadi."}</p>
    </article>
  `;
}

function renderHighlights(evaluation) {
  const perClass = evaluation.current_report.per_class || [];
  const strongest = evaluation.current_report.strongest_class;
  const weakest = evaluation.current_report.weakest_class;
  const highestRecall = [...perClass].sort((left, right) => right.recall - left.recall)[0];

  highlightGridRef.innerHTML = `
    <article class="highlight-card">
      <span>En Guclu Sinif</span>
      <strong>${strongest ? strongest.label : "-"}</strong>
      <p>${strongest ? `F1 skoru ${formatPercent(strongest.f1_score)} seviyesinde.` : "Veri bulunamadi."}</p>
    </article>
    <article class="highlight-card">
      <span>En Yuksek Recall</span>
      <strong>${highestRecall ? highestRecall.label : "-"}</strong>
      <p>${highestRecall ? `Recall degeri ${formatPercent(highestRecall.recall)}.` : "Veri bulunamadi."}</p>
    </article>
    <article class="highlight-card">
      <span>Oncelikli Iyilestirme</span>
      <strong>${weakest ? weakest.label : "-"}</strong>
      <p>${weakest ? `F1 skoru ${formatPercent(weakest.f1_score)} ile gelisim alani tasiyor.` : "Veri bulunamadi."}</p>
    </article>
  `;
}

function renderLiterature(literature) {
  if (!literature) {
    literatureSummaryRef.textContent = "Literatur verisi bulunamadi.";
    literatureBarsRef.innerHTML = "";
    return;
  }

  literatureSummaryRef.textContent = literature.summary || "Literatur verisi bulunamadi.";

  const benchmarks = literature.benchmarks || [];
  const maxAccuracy = benchmarks.reduce((maxValue, item) => Math.max(maxValue, item.accuracy || 0), 0);

  renderBars(
    literatureBarsRef,
    benchmarks.map((item) => ({
      label: `${item.short_label || item.label} ${item.year ? `(${item.year})` : ""}`.trim(),
      value: item.accuracy,
    })),
    maxAccuracy,
    formatRawPercent,
  );
}

function updateProgress() {
  const total = slideRefs.length;
  const displayIndex = currentSlideIndex + 1;
  slideCounterRef.textContent = `${displayIndex} / ${total}`;
  slideTitleRef.textContent = slideTitles[slideRefs[currentSlideIndex].id] || "Sunum";
  progressFillRef.style.width = `${(displayIndex / total) * 100}%`;
}

function updateActiveNav() {
  const activeId = slideRefs[currentSlideIndex].id;
  navLinks.forEach((link) => {
    const isActive = link.getAttribute("href") === `#${activeId}`;
    link.classList.toggle("active", isActive);
  });
}

function showSlide(index, options = {}) {
  const boundedIndex = Math.max(0, Math.min(index, slideRefs.length - 1));
  currentSlideIndex = boundedIndex;
  const activeSlide = slideRefs[currentSlideIndex];

  slideRefs.forEach((slide, slideIndex) => {
    slide.classList.toggle("is-current", slideIndex === currentSlideIndex);
  });

  updateActiveNav();
  updateProgress();

  if (!body.classList.contains("presentation-mode") && options.scroll !== false) {
    activeSlide.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function setTheme(theme) {
  const darkTheme = theme === "dark";
  body.classList.toggle("theme-dark", darkTheme);
  themeToggleButton.textContent = darkTheme ? "Beyaz Tema" : "Koyu Moda Gec";
  window.localStorage.setItem("presentation-theme", darkTheme ? "dark" : "light");
}

function setPresentationMode(enabled) {
  body.classList.toggle("presentation-mode", enabled);
  slideControlsRef.hidden = !enabled;
  presentationToggleButton.textContent = enabled ? "Akis Modu" : "Sunum Modu";
  showSlide(currentSlideIndex, { scroll: !enabled });
}

async function toggleFullscreen() {
  if (!document.fullscreenElement) {
    await document.documentElement.requestFullscreen();
    fullscreenToggleButton.textContent = "Tam Ekrandan Cik";
    return;
  }

  await document.exitFullscreen();
  fullscreenToggleButton.textContent = "Tam Ekran";
}

function applyData(payload) {
  const { project, dataset, evaluation, literature, story } = payload;
  const currentReport = evaluation.current_report;
  const strongest = currentReport.strongest_class;
  const weakest = currentReport.weakest_class;
  const training = evaluation.training || {};
  const dominantClass = dataset.dominant_class;
  const rarestClass = dataset.rarest_class;
  const reportedBestMetrics = evaluation.reported_best_metrics || {};

  titleRef.textContent = project.title;
  subtitleRef.textContent = project.subtitle;
  goalRef.textContent = project.goal;
  datasetTotalRef.textContent = formatNumber(dataset.total_images);
  currentAccuracyRef.textContent = formatPercent(currentReport.overall?.accuracy);
  reportedAccuracyRef.textContent = formatPercent(reportedBestMetrics.accuracy);
  bestValAccuracyRef.textContent = formatPercent(training.best_val_accuracy);
  imageSizeRef.textContent = `${project.image_size.width}x${project.image_size.height}`;
  renderHeroTags(project, dataset, evaluation);
  renderSpotlight(dataset, evaluation);
  renderHeroSummaryBand(dataset, evaluation);

  datasetSummaryRef.textContent =
    `Toplam ${formatNumber(dataset.total_images)} gorselden olusan FER-2013 yapisi kullanildi. ` +
    `En yogun sinif ${dominantClass}, en dusuk temsile sahip sinif ise ${rarestClass}.`;

  renderSplitOverview(dataset);
  renderBars(
    datasetBarsRef,
    Object.entries(dataset.class_totals).map(([label, value]) => ({ label, value })),
    Math.max(...Object.values(dataset.class_totals)),
    formatNumber,
  );

  renderPipeline(story);
  renderOverallMetrics(evaluation);
  renderBars(
    f1BarsRef,
    currentReport.per_class.map((item) => ({ label: item.label, value: item.f1_score })),
    1,
    formatPercent,
  );
  renderHighlights(evaluation);
  renderLiterature(literature);

  matrixImageRef.src = evaluation.confusion_matrix.image_path || "";
  matrixImageRef.hidden = !evaluation.confusion_matrix.image_path;

  resultsSummaryRef.textContent =
    `Artifact degerlendirmesinde en guclu sinif ${strongest?.label || "-"} olurken, ` +
    `en cok zorlanan sinif ${weakest?.label || "-"} olarak gorunuyor. ` +
    `Literatur karsilastirmasi, bu prototipin daha cok gelistirme payi oldugunu netlestiriyor.`;
  resultsSpotlightRef.textContent =
    `Accuracy tek basina yeterli bir olcut degil. Sinif bazli farklari, hata oruntulerini ve bu modelin HOMTECH icin nasil yorumlanabilir bir karar katmanina donustugunu birlikte okumak daha anlamli bir cerceve sunuyor.`;

  trainingSummaryRef.textContent =
    `Egitim gecmisinde en iyi validation accuracy ${formatPercent(training.best_val_accuracy)} seviyesine cikiyor. ` +
    `Bu gorunum, modelin transfer learning sonrasinda belirli bir iyilesme yakaladigini; ancak sinif dengesizligi nedeniyle hala acik gelistirme alanlari tasidigini gosteriyor.`;
  matrixCaptionRef.textContent =
    `Confusion matrix, siniflar arasindaki karisma noktalarini acik bicimde gosterir. Ozellikle ${weakest?.label || "zayif sinif"} etrafindaki dagilim, modelin en cok zorlandigi bolgeleri one cikarir.`;

  renderTrainingCards(evaluation);
  showSlide(currentSlideIndex, { scroll: false });
}

async function loadPresentationData() {
  try {
    reloadButton.disabled = true;
    const response = await fetch("/api/presentation-data");
    const payload = await response.json();
    applyData(payload);
  } finally {
    reloadButton.disabled = false;
  }
}

function syncSlideToScroll() {
  if (body.classList.contains("presentation-mode")) {
    return;
  }

  let closestIndex = 0;
  let closestDistance = Number.POSITIVE_INFINITY;

  slideRefs.forEach((slide, index) => {
    const distance = Math.abs(slide.getBoundingClientRect().top - 120);
    if (distance < closestDistance) {
      closestDistance = distance;
      closestIndex = index;
    }
  });

  if (closestIndex !== currentSlideIndex) {
    currentSlideIndex = closestIndex;
    updateActiveNav();
    updateProgress();
  }
}

navLinks.forEach((link, index) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    showSlide(index);
  });
});

reloadButton.addEventListener("click", () => {
  loadPresentationData();
});

themeToggleButton.addEventListener("click", () => {
  const nextTheme = body.classList.contains("theme-dark") ? "light" : "dark";
  setTheme(nextTheme);
});

presentationToggleButton.addEventListener("click", () => {
  setPresentationMode(!body.classList.contains("presentation-mode"));
});

fullscreenToggleButton.addEventListener("click", () => {
  toggleFullscreen();
});

prevSlideButton.addEventListener("click", () => {
  showSlide(currentSlideIndex - 1);
});

nextSlideButton.addEventListener("click", () => {
  showSlide(currentSlideIndex + 1);
});

document.addEventListener("fullscreenchange", () => {
  fullscreenToggleButton.textContent = document.fullscreenElement ? "Tam Ekrandan Cik" : "Tam Ekran";
});

document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowRight" || event.key === "PageDown") {
    event.preventDefault();
    showSlide(currentSlideIndex + 1);
  }

  if (event.key === "ArrowLeft" || event.key === "PageUp") {
    event.preventDefault();
    showSlide(currentSlideIndex - 1);
  }

  if (event.key.toLowerCase() === "f") {
    toggleFullscreen();
  }

  if (event.key.toLowerCase() === "p") {
    setPresentationMode(!body.classList.contains("presentation-mode"));
  }
});

window.addEventListener("scroll", () => {
  syncSlideToScroll();
});

setTheme(window.localStorage.getItem("presentation-theme") || "light");
updateProgress();
loadPresentationData();
