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
  hero: "Özet",
  dataset: "Veri Seti",
  pipeline: "Akış",
  results: "Sonuçlar",
  matrix: "Confusion Matrix",
  product: "Ürün Fikri",
};

let presentationData = null;
let currentSlideIndex = 0;

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "-";
  }
  return `%${(Number(value) * 100).toFixed(1)}`;
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
      <p>${dataset.name || "FER-2013"} eğitim görseli</p>
    </article>
    <article class="split-card">
      <span>Test</span>
      <strong>${formatNumber(dataset.test_total)}</strong>
      <p>Model değerlendirme görseli</p>
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
    `${project.emotion_labels.length} duygu sınıfı`,
    `${project.image_size.width}x${project.image_size.height} girdi`,
    `${formatNumber(dataset.total_images)} toplam görsel`,
    `${formatPercent(evaluation.current_report.overall.accuracy)} artifact accuracy`,
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

  spotlightTitleRef.textContent = "Teknik sonuçtan ürün hikâyesine";
  spotlightCopyRef.textContent =
    "Model çıktısı, akıllı ev bağlamında yorumlanabilir kararlar ve kullanıcı deneyimi ile birlikte ele alınıyor.";

  spotlightGridRef.innerHTML = `
    <article class="spotlight-item">
      <span>En güçlü sınıf</span>
      <strong>${strongest ? strongest.label : "-"}</strong>
    </article>
    <article class="spotlight-item">
      <span>Gelişim alanı</span>
      <strong>${weakest ? weakest.label : "-"}</strong>
    </article>
    <article class="spotlight-item">
      <span>README zirve accuracy</span>
      <strong>${formatPercent(reported.accuracy)}</strong>
    </article>
    <article class="spotlight-item">
      <span>Veri dengesizliği</span>
      <strong>${dataset.dominant_class} / ${dataset.rarest_class}</strong>
    </article>
  `;
}

function renderHeroSummaryBand(dataset, evaluation) {
  heroSummaryBandRef.innerHTML = `
    <article class="summary-band-item">
      <span>Veri kapsamı</span>
      <strong>${formatNumber(dataset.train_total)} train / ${formatNumber(dataset.test_total)} test</strong>
      <p>Benchmark veri seti üzerinden eğitim ve değerlendirme akışı kuruldu.</p>
    </article>
    <article class="summary-band-item">
      <span>Model sonucu</span>
      <strong>${formatPercent(evaluation.current_report.overall.accuracy)} accuracy</strong>
      <p>Sınıf bazlı farklılıkları okumak için F1 ve confusion matrix ile desteklendi.</p>
    </article>
    <article class="summary-band-item">
      <span>Ürün çıktısı</span>
      <strong>Duygudan senaryoya geçiş</strong>
      <p>Tahmin edilen ifade, ışık, sıcaklık, müzik ve bildirim kararlarına bağlandı.</p>
    </article>
  `;
}

function renderOverallMetrics(evaluation) {
  const overall = evaluation.current_report.overall;
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
      <p>Dengesiz sınıflara daha uygun genel kalite göstergesi</p>
    </article>
    <article class="overall-card">
      <span>Macro F1</span>
      <strong>${formatPercent(macro.f1_score)}</strong>
      <p>Sınıflar arası daha eşit bakış veren ortalama</p>
    </article>
    <article class="overall-card">
      <span>README Zirve</span>
      <strong>${formatPercent(reported.weighted_f1_score)}</strong>
      <p>Raporlanan final weighted F1</p>
    </article>
  `;
}

function renderTrainingCards(evaluation) {
  const training = evaluation.training;
  const strongest = evaluation.current_report.strongest_class;
  const weakest = evaluation.current_report.weakest_class;

  trainingCardsRef.innerHTML = `
    <article class="training-card">
      <span>En İyi Epoch</span>
      <strong>${training.best_epoch || "-"}</strong>
      <p>Val accuracy zirvesi: ${formatPercent(training.best_val_accuracy)}</p>
    </article>
    <article class="training-card">
      <span>Toplam Epoch</span>
      <strong>${training.epochs || "-"}</strong>
      <p>Kayıtlı eğitim geçmişinin toplamı</p>
    </article>
    <article class="training-card">
      <span>En Güçlü Sınıf</span>
      <strong>${strongest ? strongest.label : "-"}</strong>
      <p>${strongest ? `F1: ${formatPercent(strongest.f1_score)}` : "Sınıf metriği bulunamadı."}</p>
    </article>
    <article class="training-card">
      <span>Gelişime Açık Sınıf</span>
      <strong>${weakest ? weakest.label : "-"}</strong>
      <p>${weakest ? `F1: ${formatPercent(weakest.f1_score)}` : "Sınıf metriği bulunamadı."}</p>
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
      <span>En Güçlü Sınıf</span>
      <strong>${strongest ? strongest.label : "-"}</strong>
      <p>${strongest ? `F1 skoru ${formatPercent(strongest.f1_score)} seviyesinde.` : "Veri bulunamadı."}</p>
    </article>
    <article class="highlight-card">
      <span>En Yüksek Recall</span>
      <strong>${highestRecall ? highestRecall.label : "-"}</strong>
      <p>${highestRecall ? `Recall değeri ${formatPercent(highestRecall.recall)}.` : "Veri bulunamadı."}</p>
    </article>
    <article class="highlight-card">
      <span>Öncelikli İyileştirme</span>
      <strong>${weakest ? weakest.label : "-"}</strong>
      <p>${weakest ? `F1 skoru ${formatPercent(weakest.f1_score)} ile gelişim alanı taşıyor.` : "Veri bulunamadı."}</p>
    </article>
  `;
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
  themeToggleButton.textContent = darkTheme ? "Beyaz Tema" : "Koyu Moda Geç";
  window.localStorage.setItem("presentation-theme", darkTheme ? "dark" : "light");
}

function setPresentationMode(enabled) {
  body.classList.toggle("presentation-mode", enabled);
  slideControlsRef.hidden = !enabled;
  presentationToggleButton.textContent = enabled ? "Akış Modu" : "Sunum Modu";
  showSlide(currentSlideIndex, { scroll: !enabled });
}

async function toggleFullscreen() {
  if (!document.fullscreenElement) {
    await document.documentElement.requestFullscreen();
    fullscreenToggleButton.textContent = "Tam Ekrandan Çık";
    return;
  }

  await document.exitFullscreen();
  fullscreenToggleButton.textContent = "Tam Ekran";
}

function applyData(payload) {
  presentationData = payload;
  const { project, dataset, evaluation, story } = payload;
  const currentReport = evaluation.current_report;
  const strongest = currentReport.strongest_class;
  const weakest = currentReport.weakest_class;
  const training = evaluation.training;
  const dominantClass = dataset.dominant_class;
  const rarestClass = dataset.rarest_class;

  titleRef.textContent = project.title;
  subtitleRef.textContent = project.subtitle;
  goalRef.textContent = project.goal;
  datasetTotalRef.textContent = formatNumber(dataset.total_images);
  currentAccuracyRef.textContent = formatPercent(currentReport.overall.accuracy);
  reportedAccuracyRef.textContent = formatPercent(evaluation.reported_best_metrics.accuracy);
  bestValAccuracyRef.textContent = formatPercent(training.best_val_accuracy);
  imageSizeRef.textContent = `${project.image_size.width}x${project.image_size.height}`;
  renderHeroTags(project, dataset, evaluation);
  renderSpotlight(dataset, evaluation);
  renderHeroSummaryBand(dataset, evaluation);

  datasetSummaryRef.textContent =
    `Toplam ${formatNumber(dataset.total_images)} görselden oluşan FER-2013 yapısı kullanıldı. ` +
    `En yoğun sınıf ${dominantClass}, en düşük temsile sahip sınıf ise ${rarestClass}.`;

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

  matrixImageRef.src = evaluation.confusion_matrix.image_path || "";
  matrixImageRef.hidden = !evaluation.confusion_matrix.image_path;

  resultsSummaryRef.textContent =
    `Artifact değerlendirmesinde en güçlü sınıf ${strongest?.label || "-"} olurken, ` +
    `en çok zorlanan sınıf ${weakest?.label || "-"} olarak görünüyor. ` +
    `Bu tablo, modelin mutlu ve şaşırma gibi daha ayrık ifadelerde daha iyi sonuç verdiğini gösteriyor.`;
  resultsSpotlightRef.textContent =
    `Accuracy tek başına yeterli bir ölçüt değil. Sınıf bazlı farkları, hata örüntülerini ve bu modelin HOMTECH için nasıl yorumlanabilir bir karar katmanına dönüştüğünü birlikte okumak daha anlamlı bir çerçeve sunuyor.`;

  trainingSummaryRef.textContent =
    `Eğitim geçmişinde en iyi validation accuracy ${formatPercent(training.best_val_accuracy)} seviyesine çıkıyor. ` +
    `Bu görünüm, modelin transfer learning sonrasında belirli bir iyileşme yakaladığını; ancak sınıf dengesizliği nedeniyle hâlâ açık geliştirme alanları taşıdığını gösteriyor.`;
  matrixCaptionRef.textContent =
    `Confusion matrix, sınıflar arasındaki karışma noktalarını açık biçimde gösterir. Özellikle ${weakest?.label || "zayıf sınıf"} etrafındaki dağılım, modelin en çok zorlandığı bölgeleri öne çıkarır.`;

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
  fullscreenToggleButton.textContent = document.fullscreenElement ? "Tam Ekrandan Çık" : "Tam Ekran";
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
