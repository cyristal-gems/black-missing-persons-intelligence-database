"use strict";

const DATA_URL = "/json/cases.json";
const STATS_URL = "/json/statistics.json";
const US_STATES_URL = "/assets/us-states.geojson";

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
  })[character]);
}

function localImage(caseRecord) {
  const url = String(caseRecord.image_url || "");
  const filename = url.split("/").pop();
  return `/images/${encodeURIComponent(filename)}`;
}

function displayDate(value) {
  if (!value) return "Unknown";
  const [year, month, day] = value.split("-").map(Number);
  return new Intl.DateTimeFormat("en-US", { year: "numeric", month: "long", day: "numeric" })
    .format(new Date(year, month - 1, day));
}

function missingYear(caseRecord) {
  return String(caseRecord.missing_date || "Unknown").slice(0, 4);
}

function caseCard(caseRecord) {
  const statusClass = caseRecord.case_status === "Presumed Deceased" ? " presumed" : "";
  const location = [caseRecord.last_seen.city, caseRecord.last_seen.state].filter(Boolean).join(", ");
  return `
    <article class="case-card">
      <div class="case-card-image"><img src="${localImage(caseRecord)}" alt="${escapeHTML(caseRecord.full_name)}" loading="lazy" width="600" height="450"></div>
      <div class="case-card-body">
        <div class="card-meta"><span class="case-id">${escapeHTML(caseRecord.case_id)}</span><span class="missing-year">Missing ${escapeHTML(missingYear(caseRecord))}</span><span class="status-pill${statusClass}">${escapeHTML(caseRecord.case_status)}</span></div>
        <h3>${escapeHTML(caseRecord.full_name)}</h3>
        <p class="case-location">${escapeHTML(location)} · Missing ${escapeHTML(displayDate(caseRecord.missing_date))}</p>
        <p class="case-summary">${escapeHTML(caseRecord.case_summary_short)}</p>
      </div>
      <a class="card-link" href="/cases/${encodeURIComponent(caseRecord.case_id)}/"><span>View ${escapeHTML(caseRecord.full_name)} case profile</span></a>
    </article>`;
}

async function loadJSON(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`Unable to load ${url}`);
  return response.json();
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function renderClassificationChart(counts) {
  const chart = document.getElementById("classification-chart");
  if (!chart) return;
  const entries = Object.entries(counts);
  const maximum = Math.max(...entries.map(([, count]) => count));
  chart.innerHTML = entries.map(([label, count]) => `
    <div class="bar-row">
      <div class="bar-meta"><span>${escapeHTML(label)}</span><strong>${count}</strong></div>
      <div class="bar-track"><div class="bar-fill" style="width:${(count / maximum) * 100}%"></div></div>
    </div>`).join("");
}

function renderYearChart(cases) {
  const chart = document.getElementById("year-chart");
  if (!chart) return;
  const counts = new Map();
  cases.forEach((record) => {
    const year = Number(String(record.missing_date).slice(0, 4));
    if (Number.isInteger(year)) counts.set(year, (counts.get(year) || 0) + 1);
  });
  const recordedYears = [...counts.keys()].sort((a, b) => a - b);
  if (!recordedYears.length) {
    chart.innerHTML = '<p class="chart-empty">No dated cases are available.</p>';
    return;
  }
  const firstYear = recordedYears[0];
  const lastYear = recordedYears[recordedYears.length - 1];
  const years = Array.from({ length: lastYear - firstYear + 1 }, (_, index) => firstYear + index);
  const maximum = Math.max(...counts.values());
  chart.setAttribute("aria-label", `Cases by missing year from ${firstYear} through ${lastYear}`);
  const rangeLabel = chart.closest(".year-panel")?.querySelector(".range-label");
  if (rangeLabel) rangeLabel.textContent = `${firstYear}–${lastYear}`;
  chart.innerHTML = years.map((year) => {
    const count = counts.get(year) || 0;
    const heightLevel = count ? Math.max(1, Math.round((count / maximum) * 20)) : 0;
    const caseLabel = count === 1 ? "case" : "cases";
    const showYear = year === firstYear || year === lastYear || year % 5 === 0;
    return `<div class="year-column${count ? " has-cases" : " no-cases"}"><div class="year-bar${count ? ` height-level-${heightLevel}` : ""}"${count ? ' tabindex="0"' : ""} aria-label="${year}: ${count} ${caseLabel}">${count ? `<span class="year-count" aria-hidden="true">${count}</span><span class="year-tooltip" aria-hidden="true">${count} ${caseLabel}</span>` : ""}</div><span class="year-label" aria-hidden="true">${showYear ? year : ""}</span></div>`;
  }).join("");

  requestAnimationFrame(() => {
    if (window.matchMedia("(max-width: 760px)").matches) chart.scrollLeft = chart.scrollWidth;
  });
}

function geometryRings(geometry) {
  if (geometry.type === "Polygon") return geometry.coordinates;
  if (geometry.type === "MultiPolygon") return geometry.coordinates.flat();
  return [];
}

function albersRaw(longitude, latitude) {
  const radians = Math.PI / 180;
  const phi1 = 29.5 * radians;
  const phi2 = 45.5 * radians;
  const phi0 = 37.5 * radians;
  const lambda0 = -96 * radians;
  const phi = latitude * radians;
  const lambda = longitude * radians;
  const n = 0.5 * (Math.sin(phi1) + Math.sin(phi2));
  const c = Math.cos(phi1) ** 2 + 2 * n * Math.sin(phi1);
  const rho0 = Math.sqrt(c - 2 * n * Math.sin(phi0)) / n;
  const rho = Math.sqrt(c - 2 * n * Math.sin(phi)) / n;
  const theta = n * (lambda - lambda0);
  return [rho * Math.sin(theta), rho0 - rho * Math.cos(theta)];
}

function fittedProjection(points, box) {
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  const minX = Math.min(...xs); const maxX = Math.max(...xs);
  const minY = Math.min(...ys); const maxY = Math.max(...ys);
  const scale = Math.min(box.width / (maxX - minX), box.height / (maxY - minY));
  const offsetX = box.x + (box.width - (maxX - minX) * scale) / 2;
  const offsetY = box.y + (box.height - (maxY - minY) * scale) / 2;
  return ([x, y]) => [offsetX + (x - minX) * scale, offsetY + (maxY - y) * scale];
}

function insetProjection(bounds, box, normalizeLongitude = (value) => value) {
  const [minLongitude, minLatitude, maxLongitude, maxLatitude] = bounds;
  const scale = Math.min(box.width / (maxLongitude - minLongitude), box.height / (maxLatitude - minLatitude));
  const offsetX = box.x + (box.width - (maxLongitude - minLongitude) * scale) / 2;
  const offsetY = box.y + (box.height - (maxLatitude - minLatitude) * scale) / 2;
  return ([longitude, latitude]) => {
    const normalized = normalizeLongitude(longitude);
    return [offsetX + (normalized - minLongitude) * scale, offsetY + (maxLatitude - latitude) * scale];
  };
}

function renderMap(cases, geography) {
  const map = document.getElementById("case-map");
  const tooltip = document.getElementById("map-tooltip");
  if (!map || !tooltip) return;
  const namespace = "http://www.w3.org/2000/svg";
  const viewport = document.createElementNS(namespace, "g");
  viewport.setAttribute("class", "map-viewport");
  map.appendChild(viewport);
  const stateCodes = new Set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC".split(" "));
  const states = geography.features.filter((feature) => stateCodes.has(feature.properties.STUSAB));
  const contiguous = states.filter((feature) => !["AK", "HI"].includes(feature.properties.STUSAB));
  const contiguousRawPoints = contiguous.flatMap((feature) => geometryRings(feature.geometry).flat().map(([longitude, latitude]) => albersRaw(longitude, latitude)));
  const contiguousFit = fittedProjection(contiguousRawPoints, { x: 80, y: 18, width: 900, height: 485 });
  const projectContiguous = ([longitude, latitude]) => contiguousFit(albersRaw(longitude, latitude));
  const projectAlaska = insetProjection([-190, 51, -129, 72], { x: 20, y: 455, width: 235, height: 145 }, (longitude) => longitude > 0 ? longitude - 360 : longitude);
  const projectHawaii = insetProjection([-161, 18.5, -154, 22.5], { x: 275, y: 520, width: 140, height: 70 });
  const projectionFor = (code) => code === "AK" ? projectAlaska : code === "HI" ? projectHawaii : projectContiguous;

  states.forEach((feature) => {
    const code = feature.properties.STUSAB;
    const project = projectionFor(code);
    const pathData = geometryRings(feature.geometry).map((ring) => ring.map((coordinate, index) => {
      const [x, y] = project(coordinate);
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ") + " Z").join(" ");
    const path = document.createElementNS(namespace, "path");
    path.setAttribute("d", pathData);
    path.setAttribute("class", "map-state");
    const title = document.createElementNS(namespace, "title");
    title.textContent = feature.properties.BASENAME;
    path.appendChild(title);
    viewport.appendChild(path);
  });

  [[15, 448, 245, 160], [270, 515, 150, 82]].forEach(([x, y, width, height]) => {
    const border = document.createElementNS(namespace, "rect");
    border.setAttribute("x", x); border.setAttribute("y", y); border.setAttribute("width", width); border.setAttribute("height", height); border.setAttribute("rx", "8"); border.setAttribute("class", "map-inset-border"); viewport.appendChild(border);
  });
  [[28, 472, "Alaska"], [283, 540, "Hawaii"]].forEach(([x, y, text]) => {
    const label = document.createElementNS(namespace, "text");
    label.setAttribute("x", x); label.setAttribute("y", y); label.setAttribute("class", "map-inset-label"); label.textContent = text; viewport.appendChild(label);
  });

  const coordinateGroups = new Map();
  cases.forEach((record) => {
    const key = record.last_seen.state === "New York"
      ? "state:New York"
      : `${record.last_seen.latitude},${record.last_seen.longitude}`;
    if (!coordinateGroups.has(key)) coordinateGroups.set(key, []);
    coordinateGroups.get(key).push(record);
  });
  const formatMapLocation = (record) => record.last_seen.city === record.last_seen.state
    ? record.last_seen.state
    : `${record.last_seen.city}, ${record.last_seen.state}`;
  const showTooltip = (x, y, content, key = "") => {
    const mapRect = map.getBoundingClientRect();
    const wrapRect = map.parentElement.getBoundingClientRect();
    const scaledX = ((x - view.x) / view.width) * mapRect.width;
    const scaledY = ((y - view.y) / view.height) * mapRect.height;
    tooltip.innerHTML = content;
    tooltip.dataset.clusterKey = key;
    const maximumLeft = Math.max(10, mapRect.width - 330);
    tooltip.style.left = `${mapRect.left - wrapRect.left + Math.min(maximumLeft, Math.max(10, scaledX + 10))}px`;
    tooltip.style.top = `${mapRect.top - wrapRect.top + Math.max(10, scaledY - 45)}px`;
    tooltip.hidden = false;
  };
  const clusterNodes = [];
  coordinateGroups.forEach((records, coordinateKey) => {
    const record = records[0];
    const stateGroup = coordinateKey.startsWith("state:");
    const longitude = stateGroup
      ? records.reduce((sum, item) => sum + item.last_seen.longitude, 0) / records.length
      : record.last_seen.longitude;
    const latitude = stateGroup
      ? records.reduce((sum, item) => sum + item.last_seen.latitude, 0) / records.length
      : record.last_seen.latitude;
    if (typeof longitude !== "number" || typeof latitude !== "number") return;
    const state = record.last_seen.state;
    const project = state === "Alaska" ? projectAlaska : state === "Hawaii" ? projectHawaii : projectContiguous;
    const [x, y] = project([longitude, latitude]);
    if (records.length === 1) {
      const anchor = document.createElementNS(namespace, "a");
      anchor.setAttribute("href", `/cases/${record.case_id}/`);
      anchor.setAttribute("aria-label", `${record.full_name}, ${formatMapLocation(record)}`);
      const marker = document.createElementNS(namespace, "circle");
      marker.setAttribute("cx", String(x)); marker.setAttribute("cy", String(y)); marker.setAttribute("r", "7"); marker.setAttribute("data-base-radius", "7"); marker.setAttribute("class", "map-marker");
      const show = (event) => {
        showTooltip(x, y, `<a class="map-tooltip-name" href="/cases/${encodeURIComponent(record.case_id)}/">${escapeHTML(record.full_name)}</a><span class="map-tooltip-meta">${escapeHTML(formatMapLocation(record))} · ${escapeHTML(record.case_classification)}</span><p class="map-tooltip-summary">${escapeHTML(record.case_summary_short)}</p>`);
        event.stopPropagation();
      };
      anchor.addEventListener("mouseenter", show); anchor.addEventListener("focus", show);
      anchor.appendChild(marker); viewport.appendChild(anchor);
      return;
    }
    const cluster = document.createElementNS(namespace, "g");
    cluster.setAttribute("class", "map-cluster"); cluster.setAttribute("tabindex", "0"); cluster.setAttribute("role", "button");
    const locationLabel = stateGroup ? state : formatMapLocation(record);
    cluster.setAttribute("aria-label", `${records.length} cases in ${locationLabel}`);
    const marker = document.createElementNS(namespace, "circle");
    marker.setAttribute("cx", String(x)); marker.setAttribute("cy", String(y)); marker.setAttribute("r", "10"); marker.setAttribute("data-base-radius", "10"); marker.setAttribute("class", "map-marker map-cluster-marker");
    const count = document.createElementNS(namespace, "text");
    count.setAttribute("x", String(x)); count.setAttribute("y", String(y)); count.setAttribute("class", "map-cluster-count"); count.setAttribute("text-anchor", "middle"); count.setAttribute("dominant-baseline", "central"); count.setAttribute("aria-hidden", "true"); count.textContent = String(records.length);
    const showCluster = (event) => {
      const items = records.map((item) => `<li><a href="/cases/${encodeURIComponent(item.case_id)}/">${escapeHTML(item.full_name)}</a><span class="map-cluster-location">${escapeHTML(formatMapLocation(item))}</span><p>${escapeHTML(item.case_summary_short)}</p></li>`).join("");
      const locationCount = new Set(records.map((item) => `${item.last_seen.city},${item.last_seen.state}`)).size;
      const clusterDescription = stateGroup
        ? `${records.length} cases across ${locationCount} recorded locations`
        : `${records.length} cases at this generalized location`;
      showTooltip(x, y, `<strong>${escapeHTML(locationLabel)}</strong><span>${clusterDescription}</span><ul class="map-cluster-list">${items}</ul>`, coordinateKey);
      event.stopPropagation();
    };
    cluster.addEventListener("mouseenter", showCluster); cluster.addEventListener("click", showCluster); cluster.addEventListener("focus", showCluster);
    cluster.appendChild(marker); cluster.appendChild(count); clusterNodes.push(cluster);
  });
  clusterNodes.forEach((cluster) => viewport.appendChild(cluster));
  tooltip.addEventListener("click", (event) => event.stopPropagation());

  const fullView = { x: 0, y: 0, width: 1000, height: 620 };
  const minimumWidth = 220;
  let view = { ...fullView };
  let viewAnimation = null;
  const zoomInButton = document.getElementById("map-zoom-in");
  const zoomOutButton = document.getElementById("map-zoom-out");
  const applyView = () => {
    map.setAttribute("viewBox", `${view.x} ${view.y} ${view.width} ${view.height}`);
    const scale = view.width / fullView.width;
    map.querySelectorAll(".map-marker").forEach((marker) => marker.setAttribute("r", String(Number(marker.dataset.baseRadius || 7) * scale)));
    map.querySelectorAll(".map-cluster-count").forEach((count) => { count.style.fontSize = `${9 * scale}px`; });
    if (zoomInButton) zoomInButton.disabled = view.width <= minimumWidth + 1;
    if (zoomOutButton) zoomOutButton.disabled = view.width >= fullView.width - 1;
  };
  const animateView = (target, duration = 280) => {
    if (viewAnimation) cancelAnimationFrame(viewAnimation);
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      view = { ...target }; applyView(); return;
    }
    const start = { ...view };
    const startedAt = performance.now();
    const frame = (now) => {
      const progress = Math.min(1, (now - startedAt) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      view = {
        x: start.x + (target.x - start.x) * eased,
        y: start.y + (target.y - start.y) * eased,
        width: start.width + (target.width - start.width) * eased,
        height: start.height + (target.height - start.height) * eased
      };
      applyView();
      if (progress < 1) viewAnimation = requestAnimationFrame(frame);
      else viewAnimation = null;
    };
    viewAnimation = requestAnimationFrame(frame);
  };
  const clampView = (target) => ({
    x: Math.min(fullView.width - target.width, Math.max(0, target.x)),
    y: Math.min(fullView.height - target.height, Math.max(0, target.y)),
    width: target.width,
    height: target.height
  });
  const zoomAt = (factor) => {
    const nextWidth = Math.min(fullView.width, Math.max(minimumWidth, view.width * factor));
    const nextHeight = nextWidth * (fullView.height / fullView.width);
    const centerX = view.x + view.width / 2;
    const centerY = view.y + view.height / 2;
    animateView(clampView({
      x: centerX - nextWidth / 2,
      y: centerY - nextHeight / 2,
      width: nextWidth,
      height: nextHeight
    }));
  };
  const panBy = (xRatio, yRatio) => {
    if (view.width >= fullView.width - 1) return;
    animateView(clampView({
      x: view.x + view.width * xRatio,
      y: view.y + view.height * yRatio,
      width: view.width,
      height: view.height
    }), 200);
  };
  zoomInButton?.addEventListener("click", () => zoomAt(0.62));
  zoomOutButton?.addEventListener("click", () => zoomAt(1 / 0.62));
  document.getElementById("map-reset")?.addEventListener("click", () => animateView(fullView));
  map.addEventListener("keydown", (event) => {
    const actions = {
      "+": () => zoomAt(0.62), "=": () => zoomAt(0.62),
      "-": () => zoomAt(1 / 0.62), "_": () => zoomAt(1 / 0.62),
      ArrowLeft: () => panBy(-0.25, 0), ArrowRight: () => panBy(0.25, 0),
      ArrowUp: () => panBy(0, -0.25), ArrowDown: () => panBy(0, 0.25),
      Home: () => animateView(fullView)
    };
    if (actions[event.key]) { event.preventDefault(); actions[event.key](); }
  });
  let dragStart = null;
  let dragMoved = false;
  map.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    if (viewAnimation) { cancelAnimationFrame(viewAnimation); viewAnimation = null; }
    dragStart = { clientX: event.clientX, clientY: event.clientY, x: view.x, y: view.y };
    dragMoved = false;
    map.setPointerCapture(event.pointerId);
    map.classList.add("is-panning");
  });
  map.addEventListener("pointermove", (event) => {
    if (!dragStart || view.width >= fullView.width - 1) return;
    const rect = map.getBoundingClientRect();
    const dx = (event.clientX - dragStart.clientX) * (view.width / rect.width);
    const dy = (event.clientY - dragStart.clientY) * (view.height / rect.height);
    if (Math.abs(event.clientX - dragStart.clientX) > 3 || Math.abs(event.clientY - dragStart.clientY) > 3) dragMoved = true;
    view = clampView({ x: dragStart.x - dx, y: dragStart.y - dy, width: view.width, height: view.height });
    tooltip.hidden = true;
    applyView();
  });
  const endPan = () => { dragStart = null; map.classList.remove("is-panning"); };
  map.addEventListener("pointerup", endPan);
  map.addEventListener("pointercancel", endPan);
  map.addEventListener("click", (event) => {
    if (dragMoved) { event.preventDefault(); event.stopPropagation(); dragMoved = false; return; }
    if (!event.target.closest(".map-cluster")) tooltip.hidden = true;
  }, true);
  applyView();
}

async function initDashboard() {
  const [casePayload, stats, geography] = await Promise.all([loadJSON(DATA_URL), loadJSON(STATS_URL), loadJSON(US_STATES_URL)]);
  const cases = casePayload.cases;
  setText("scope-cases", stats.total_cases);
  setText("scope-states", Object.keys(stats.by_state).length);
  setText("scope-years", `${stats.missing_date_range.earliest_year}–${stats.missing_date_range.latest_year}`);
  setText("scope-geocoded", `${Math.round((stats.geocoded_cases / stats.total_cases) * 100)}%`);
  setText("metric-men", stats.by_classification["Adult Man"] || 0);
  setText("metric-women", stats.by_classification["Adult Woman"] || 0);
  setText("metric-children", stats.by_classification.Child || 0);
  setText("metric-lgbtq", stats.by_classification["LGBTQ+"] || 0);
  renderClassificationChart(stats.by_case_classification);
  renderYearChart(cases);
  renderMap(cases, geography);
}

function addOptions(select, values) {
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value; option.textContent = value; select.appendChild(option);
  });
}

async function initDirectory() {
  const payload = await loadJSON(DATA_URL);
  const allCases = payload.cases;
  const directory = document.getElementById("case-directory");
  const noResults = document.getElementById("no-results");
  const search = document.getElementById("case-search");
  const state = document.getElementById("state-filter");
  const classification = document.getElementById("classification-filter");
  const status = document.getElementById("status-filter");
  const year = document.getElementById("year-filter");
  const sort = document.getElementById("sort-filter");
  addOptions(state, [...new Set(allCases.map((record) => record.last_seen.state))].sort());
  addOptions(classification, [...new Set(allCases.map((record) => record.classification))].sort());
  addOptions(status, [...new Set(allCases.map((record) => record.case_status))].sort());
  addOptions(year, [...new Set(allCases.map(missingYear))].sort((a, b) => b.localeCompare(a)));
  setText("generated-date", displayDate(payload.generated_on));

  const render = () => {
    const query = search.value.trim().toLocaleLowerCase();
    const queryTerms = query.split(/\s+/).filter(Boolean);
    let filtered = allCases.filter((record) => {
      const searchable = [record.case_id, record.full_name, record.last_seen.city, record.last_seen.state, record.case_classification].join(" ").toLocaleLowerCase();
      return (queryTerms.length === 0 || queryTerms.every((term) => searchable.includes(term))) && (!state.value || record.last_seen.state === state.value) && (!classification.value || record.classification === classification.value) && (!status.value || record.case_status === status.value) && (!year.value || missingYear(record) === year.value);
    });
    filtered = [...filtered].sort((a, b) => {
      const yearOrder = sort.value === "oldest" ? a.missing_date.localeCompare(b.missing_date) : b.missing_date.localeCompare(a.missing_date);
      if (missingYear(a) !== missingYear(b)) return yearOrder;
      if (sort.value === "name") return a.full_name.localeCompare(b.full_name);
      if (sort.value === "case_id") return a.case_id.localeCompare(b.case_id);
      return yearOrder;
    });
    setText("result-count", filtered.length);
    const groups = new Map();
    filtered.forEach((record) => {
      const caseYear = missingYear(record);
      if (!groups.has(caseYear)) groups.set(caseYear, []);
      groups.get(caseYear).push(record);
    });
    directory.innerHTML = [...groups.entries()].map(([caseYear, records]) => `
      <section class="year-group" aria-labelledby="year-${escapeHTML(caseYear)}">
        <div class="year-group-heading"><h2 id="year-${escapeHTML(caseYear)}">${escapeHTML(caseYear)}</h2><span>${records.length} ${records.length === 1 ? "case" : "cases"}</span></div>
        <div class="case-grid directory-grid">${records.map(caseCard).join("")}</div>
      </section>`).join("");
    noResults.hidden = filtered.length !== 0;
  };

  [search, state, classification, status, year, sort].forEach((control) => control.addEventListener(control === search ? "input" : "change", render));
  document.getElementById("reset-filters").addEventListener("click", () => {
    search.value = ""; state.value = ""; classification.value = ""; status.value = ""; year.value = ""; sort.value = "newest"; render(); search.focus();
  });
  render();
}

document.querySelectorAll("[data-current-year]").forEach((element) => { element.textContent = new Date().getFullYear(); });
const page = document.body.dataset.page;
if (page === "dashboard") initDashboard().catch(() => {
  const featured = document.getElementById("featured-cases");
  if (featured) featured.innerHTML = '<div class="empty-state"><h2>Data unavailable</h2><p>Please refresh the page to try again.</p></div>';
});
if (page === "cases") initDirectory().catch(() => {
  const noResults = document.getElementById("no-results");
  if (noResults) { noResults.hidden = false; noResults.querySelector("h2").textContent = "Unable to load case data"; }
});
