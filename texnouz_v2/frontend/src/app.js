/* Texnouz v2 Frontend */
const API_BASE = window.location.origin;

// ===== STATE =====
let state = {
  token: localStorage.getItem("token"),
  operator: JSON.parse(localStorage.getItem("operator") || "null"),
  activeShift: null,
  fuelTypes: [],
  trkStatus: [],
  activeOrderId: null,
  activePistId: null,
  sseSource: null,
};

// ===== API =====
async function api(method, path, body = null) {
  const opts = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
    },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(API_BASE + path, opts);
  if (res.status === 401) { doLogout(); return null; }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ===== AUTH =====
async function doLogin() {
  const pw = document.getElementById("loginPassword").value;
  try {
    const data = await api("POST", "/auth/login", { password: pw });
    if (!data) return;
    state.token = data.token;
    state.operator = { id: data.operator_id, name: data.name };
    localStorage.setItem("token", data.token);
    localStorage.setItem("operator", JSON.stringify(state.operator));
    document.getElementById("loginModal").classList.add("hidden");
    document.getElementById("app").classList.remove("hidden");
    document.getElementById("loginError").classList.add("hidden");
    await initApp();
  } catch (e) {
    document.getElementById("loginError").classList.remove("hidden");
    document.getElementById("loginError").textContent = e.message;
  }
}

function doLogout() {
  state.token = null;
  state.operator = null;
  localStorage.removeItem("token");
  localStorage.removeItem("operator");
  if (state.sseSource) state.sseSource.close();
  document.getElementById("loginModal").classList.remove("hidden");
  document.getElementById("app").classList.add("hidden");
}

// ===== INIT =====
async function initApp() {
  // Operator nomi
  document.getElementById("headerOperator").textContent =
    "👤 " + (state.operator?.name || "");

  // Soat
  setInterval(() => {
    document.getElementById("headerTime").textContent =
      new Date().toLocaleTimeString("uz-UZ");
  }, 1000);

  // Ma'lumot yuklash
  await loadFuelTypes();
  await loadActiveShift();
  startSSE();
  await loadPriceList();
}

async function loadFuelTypes() {
  try {
    state.fuelTypes = await api("GET", "/fuel/types") || [];
    populateFuelSelect();
  } catch (e) {}
}

async function loadActiveShift() {
  try {
    const data = await api("GET", "/shifts/active");
    if (!data) return;
    state.activeShift = data.active ? data.shift : null;
    updateShiftUI();
  } catch (e) {}
}

function updateShiftUI() {
  const s = state.activeShift;
  const headerEl = document.getElementById("headerShift");
  const infoEl = document.getElementById("shiftInfo");
  const btnOpen = document.getElementById("btnOpenShift");
  const btnClose = document.getElementById("btnCloseShift");

  if (s) {
    headerEl.textContent = `Smena #${s.change_id}`;
    headerEl.className = "text-sm bg-green-600 px-3 py-1 rounded-full";
    infoEl.innerHTML = `
      <div class="space-y-2 text-sm">
        <div><span class="text-gray-500">ID:</span> <strong>#${s.change_id}</strong></div>
        <div><span class="text-gray-500">Boshlandi:</span> ${s.start?.replace("T", " ").slice(0, 19)}</div>
        <div class="text-green-600 font-semibold">✓ Faol smena</div>
      </div>`;
    btnOpen.classList.add("hidden");
    btnClose.classList.remove("hidden");
  } else {
    headerEl.textContent = "Smena yo'q";
    headerEl.className = "text-sm bg-red-500 px-3 py-1 rounded-full";
    infoEl.innerHTML = `<p class="text-gray-500">Faol smena yo'q</p>`;
    btnOpen.classList.remove("hidden");
    btnClose.classList.add("hidden");
  }
}

// ===== TRK SSE =====
function startSSE() {
  if (state.sseSource) state.sseSource.close();
  const url = `${API_BASE}/trk/events`;
  const src = new EventSource(url + `?token=${state.token}`);
  src.onmessage = (e) => {
    try {
      state.trkStatus = JSON.parse(e.data);
      renderTRKGrid();
    } catch (_) {}
  };
  src.onerror = () => {
    // fallback polling
    setTimeout(() => pollTRKStatus(), 2000);
  };
  state.sseSource = src;
}

async function pollTRKStatus() {
  try {
    state.trkStatus = await api("GET", "/trk/status") || [];
    renderTRKGrid();
  } catch (_) {}
}

function renderTRKGrid() {
  const grid = document.getElementById("trkGrid");
  if (!state.trkStatus.length) {
    grid.innerHTML = `<div class="col-span-4 text-center text-gray-400 py-8">TRK ma'lumoti yo'q</div>`;
    return;
  }

  const statusColors = {
    0: "bg-gray-100 border-gray-300 text-gray-600",
    1: "bg-yellow-100 border-yellow-400 text-yellow-800",
    2: "bg-blue-100 border-blue-500 text-blue-800",
    3: "bg-green-100 border-green-500 text-green-800",
    4: "bg-red-100 border-red-500 text-red-800",
  };
  const statusIcons = { 0: "⬜", 1: "🟡", 2: "🔵", 3: "🟢", 4: "🔴" };
  const statusLabels = { 0: "Bo'sh", 1: "Qurollangan", 2: "Quyilmoqda", 3: "Tayyor", 4: "Xato" };

  grid.innerHTML = state.trkStatus.map(s => {
    const cls = statusColors[s.status] || statusColors[0];
    const icon = statusIcons[s.status] || "⬜";
    const label = statusLabels[s.status] || s.status_name;
    const isActive = state.activePistId === s.pist_id;
    return `
      <div class="border-2 rounded-xl p-4 cursor-pointer transition hover:shadow-md ${cls} ${isActive ? 'ring-2 ring-blue-500' : ''}"
           onclick="selectGun(${s.pist_id})">
        <div class="text-2xl mb-1">${icon}</div>
        <div class="font-bold text-lg">Pistolet ${s.pist_id}</div>
        <div class="text-sm font-medium">${label}</div>
        ${s.liters > 0 ? `<div class="text-xl font-mono mt-1">${s.liters.toFixed(2)} L</div>` : ''}
        ${s.status === 3 ? `<button onclick="event.stopPropagation(); showPaymentForGun(${s.pist_id})"
          class="mt-2 w-full bg-green-600 text-white text-xs py-1 rounded">✓ To'lov</button>` : ''}
      </div>
    `;
  }).join('');
}

function selectGun(pistId) {
  state.activePistId = pistId;
  document.getElementById("selPistolet").value = pistId;
  renderTRKGrid();
}

// ===== FUEL SELECT =====
function populateFuelSelect() {
  const sel = document.getElementById("selGasType");
  sel.innerHTML = state.fuelTypes.map(g =>
    `<option value="${g.gas_id}">${g.name} — ${Number(g.price).toLocaleString()} so'm</option>`
  ).join('');

  const pistSel = document.getElementById("selPistolet");
  const pists = [...new Set(state.trkStatus.map(s => s.pist_id))];
  if (pists.length) {
    pistSel.innerHTML = pists.map(p => `<option value="${p}">Pistolet ${p}</option>`).join('');
  }
}

function updatePresetLabel() {
  const type = document.getElementById("selPresetType").value;
  const labels = { liters: "Litr", money: "Pul (so'm)", full: "—" };
  document.getElementById("presetLabel").textContent = labels[type] || "Miqdor";
  document.getElementById("inpPreset").disabled = type === "full";
}

// ===== DISPENSE =====
async function startDispense() {
  if (!state.activeShift) {
    alert("Avval smenani oching!");
    return;
  }
  const pistId = parseInt(document.getElementById("selPistolet").value);
  const gasId = parseInt(document.getElementById("selGasType").value);
  const presetType = document.getElementById("selPresetType").value;
  const presetVal = parseFloat(document.getElementById("inpPreset").value) || 0;
  const payType = document.getElementById("selPayment").value;
  const carNum = document.getElementById("inpCarNumber").value.trim().toUpperCase();

  // Sisterna ID ni gasId dan topish
  const trk = state.trkStatus.find(s => s.pist_id === pistId);
  const cisternId = 1; // TODO: TRK config dan olish

  const body = {
    pistolet_id: pistId,
    gas_id: gasId,
    cistern_id: cisternId,
    payment_type: payType,
    car_number: carNum || null,
    preset_liters: presetType === "liters" ? presetVal : null,
    preset_money: presetType === "money" ? presetVal : null,
  };

  try {
    const order = await api("POST", "/dispense/order", body);
    if (!order) return;
    state.activeOrderId = order.data_id;
    state.activePistId = pistId;
    document.getElementById("btnStart").classList.add("hidden");
    document.getElementById("btnStop").classList.remove("hidden");
    addTxLog(`▶ Pistolet ${pistId}: quyish boshlandi (buyurtma #${order.data_id})`);
  } catch (e) {
    alert("Xato: " + e.message);
  }
}

async function stopDispense() {
  if (!state.activePistId) return;
  try {
    await api("POST", `/trk/stop/${state.activePistId}`);
    if (state.activeOrderId) {
      await api("POST", `/dispense/${state.activeOrderId}/cancel`);
    }
    state.activeOrderId = null;
    document.getElementById("btnStart").classList.remove("hidden");
    document.getElementById("btnStop").classList.add("hidden");
    addTxLog(`■ Pistolet ${state.activePistId}: to'xtatildi`);
  } catch (e) {
    alert(e.message);
  }
}

async function showPaymentForGun(pistId) {
  // TRK dan yakuniy litr olish
  const gunStat = state.trkStatus.find(s => s.pist_id === pistId);
  const liters = gunStat?.liters || 0;

  // ActiveOrder topish (pistId bo'yicha)
  // For simplicity, use state.activeOrderId if matches
  const orderId = state.activeOrderId;
  if (!orderId) return;

  // Gaz narxi
  const gasId = parseInt(document.getElementById("selGasType").value);
  const gas = state.fuelTypes.find(g => g.gas_id === gasId);
  const price = gas?.price || 0;
  const total = liters * price;

  document.getElementById("paymentInfo").innerHTML = `
    <div><span class="text-gray-500">Pistolet:</span> <strong>${pistId}</strong></div>
    <div><span class="text-gray-500">Litr:</span> <strong>${liters.toFixed(2)} L</strong></div>
    <div><span class="text-gray-500">Narx:</span> <strong>${Number(price).toLocaleString()} so'm/L</strong></div>
    <div class="text-lg font-bold text-blue-700 pt-2">Jami: ${total.toLocaleString()} so'm</div>
  `;
  document.getElementById("payModalCash").value = Math.ceil(total);
  document.getElementById("payModalBank").value = "";
  document.getElementById("paymentModal").dataset.orderId = orderId;
  document.getElementById("paymentModal").dataset.liters = liters;
  document.getElementById("paymentModal").classList.remove("hidden");
  document.getElementById("paymentModal").classList.add("flex");
}

async function confirmPayment() {
  const orderId = document.getElementById("paymentModal").dataset.orderId;
  const liters = parseFloat(document.getElementById("paymentModal").dataset.liters) || 0;
  const cash = parseFloat(document.getElementById("payModalCash").value) || 0;
  const bank = parseFloat(document.getElementById("payModalBank").value) || 0;

  try {
    const result = await api("POST", `/dispense/${orderId}/complete`, {
      liters_actual: liters,
      money_cash: cash,
      money_bank: bank,
    });
    addTxLog(`✓ #${orderId}: ${liters.toFixed(2)}L — naqd: ${cash.toLocaleString()}, bank: ${bank.toLocaleString()}`);
    closePaymentModal();
    state.activeOrderId = null;
    document.getElementById("btnStart").classList.remove("hidden");
    document.getElementById("btnStop").classList.add("hidden");
  } catch (e) {
    alert("To'lov xatosi: " + e.message);
  }
}

function closePaymentModal() {
  document.getElementById("paymentModal").classList.add("hidden");
  document.getElementById("paymentModal").classList.remove("flex");
}

function addTxLog(msg) {
  const log = document.getElementById("txLog");
  const item = document.createElement("div");
  item.className = "flex items-center gap-2 text-sm text-gray-700 border-b pb-2";
  const time = new Date().toLocaleTimeString("uz-UZ");
  item.innerHTML = `<span class="text-gray-400 text-xs">${time}</span> ${msg}`;
  if (log.firstChild?.tagName === 'P') log.innerHTML = '';
  log.insertBefore(item, log.firstChild);
  if (log.children.length > 20) log.removeChild(log.lastChild);
}

// ===== SHIFT MANAGEMENT =====
async function openShift() {
  try {
    const res = await api("POST", "/shifts/open");
    if (!res) return;
    state.activeShift = res.shift;
    updateShiftUI();
    addTxLog(`📋 Smena #${res.shift.change_id} ochildi`);
  } catch (e) {
    alert("Smena ochmadi: " + e.message);
  }
}

async function closeShiftConfirm() {
  if (!state.activeShift) return;
  if (!confirm(`Smena #${state.activeShift.change_id} ni yopishni tasdiqlaysizmi?`)) return;
  try {
    const res = await api("POST", `/shifts/${state.activeShift.change_id}/close`, { close_type: 0 });
    state.activeShift = null;
    updateShiftUI();
    if (res.summary) showShiftSummary(res.summary);
    addTxLog(`📋 Smena yopildi`);
  } catch (e) {
    alert("Smena yopmadi: " + e.message);
  }
}

function showShiftSummary(summary) {
  const lines = summary.gas_summary.map(g =>
    `<tr><td class="py-1 pr-4">Gaz #${g.gas_id}</td><td>${g.liters.toFixed(2)} L</td><td>${g.cash.toLocaleString()}</td><td>${g.bank.toLocaleString()}</td></tr>`
  ).join('');
  const msg = `
    SMENA HISOBOTI
    ═══════════════
    Naqd:  ${summary.total_cash.toLocaleString()} so'm
    Bank:  ${summary.total_bank.toLocaleString()} so'm
    Talon: ${summary.total_talon.toLocaleString()} so'm
    ───────────────
    JAMI:  ${(summary.total_cash + summary.total_bank + summary.total_talon + summary.total_credit).toLocaleString()} so'm
  `;
  alert(msg);
}

// ===== REPORTS =====
async function loadCurrentReport() {
  try {
    const data = await api("GET", "/reports/current");
    const el = document.getElementById("reportContent");
    if (data.error) { el.textContent = data.error; return; }

    const rows = data.gas_summary.map(g => `
      <tr class="border-b">
        <td class="py-2 pr-4">Gaz #${g.gas_id}</td>
        <td class="py-2 pr-4">${g.liters.toFixed(2)} L</td>
        <td class="py-2 pr-4">${g.cash.toLocaleString()}</td>
        <td class="py-2 pr-4">${g.bank.toLocaleString()}</td>
        <td class="py-2">${g.talon.toLocaleString()}</td>
      </tr>`).join('');

    el.innerHTML = `
      <table class="w-full text-sm">
        <thead class="text-xs text-gray-500 uppercase">
          <tr><th class="text-left py-1 pr-4">Gaz</th><th>Litr</th><th>Naqd</th><th>Bank</th><th>Talon</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      <div class="mt-4 pt-4 border-t grid grid-cols-2 gap-2 text-sm">
        <div>Naqd: <strong>${data.total_cash.toLocaleString()}</strong></div>
        <div>Bank: <strong>${data.total_bank.toLocaleString()}</strong></div>
        <div>Talon: <strong>${data.total_talon.toLocaleString()}</strong></div>
        <div class="text-blue-700 font-bold">JAMI: ${(data.total_cash+data.total_bank+data.total_talon+data.total_credit).toLocaleString()}</div>
      </div>`;
  } catch (e) {
    document.getElementById("reportContent").textContent = "Xato: " + e.message;
  }
}

// ===== ADMIN / PRICE =====
async function loadPriceList() {
  try {
    const types = await api("GET", "/fuel/types") || [];
    const el = document.getElementById("priceList");
    el.innerHTML = types.map(g => `
      <div class="flex items-center gap-3 border-b pb-3">
        <span class="flex-1 font-medium">${g.name}</span>
        <input type="number" step="100" value="${g.price}" id="price_${g.gas_id}"
          class="border rounded px-3 py-1 w-32 text-sm">
        <button onclick="updatePrice(${g.gas_id})"
          class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
          Saqlash
        </button>
      </div>
    `).join('');
  } catch (e) {}
}

async function updatePrice(gasId) {
  const val = parseFloat(document.getElementById(`price_${gasId}`).value);
  try {
    await api("POST", "/fuel/price", { gas_id: gasId, price: val });
    alert("Narx yangilandi!");
    await loadFuelTypes();
    await loadPriceList();
  } catch (e) {
    alert("Xato: " + e.message);
  }
}

// ===== TABS =====
function showTab(name) {
  ["cashier", "shift", "report", "admin"].forEach(t => {
    document.getElementById(`tab-${t}-content`).classList.add("hidden");
    document.getElementById(`tab-${t}`).classList.remove("border-b-2", "border-blue-600", "text-blue-600");
    document.getElementById(`tab-${t}`).classList.add("text-gray-600");
  });
  document.getElementById(`tab-${name}-content`).classList.remove("hidden");
  document.getElementById(`tab-${name}`).classList.add("border-b-2", "border-blue-600", "text-blue-600");
  document.getElementById(`tab-${name}`).classList.remove("text-gray-600");

  if (name === "shift") loadActiveShift();
  if (name === "report") loadCurrentReport();
  if (name === "admin") loadPriceList();
}

// ===== BOOTSTRAP =====
document.addEventListener("DOMContentLoaded", () => {
  if (state.token && state.operator) {
    document.getElementById("loginModal").classList.add("hidden");
    document.getElementById("app").classList.remove("hidden");
    initApp();
  }
});
