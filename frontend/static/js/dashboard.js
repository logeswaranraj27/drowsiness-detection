/* dashboard.js — main app logic */

// ── i18n (dashboard strings) ───────────────────────────────────────────────────
const T = {
  en: {
    nav_main:"Main", nav_dashboard:"Dashboard", nav_live:"Live Detection",
    nav_history:"Session History", nav_account:"Account", nav_profile:"Profile",
    dashboard_title:"Overview", dashboard_sub:"Your drowsiness detection activity at a glance",
    stat_sessions:"Total Sessions", stat_sessions_sub:"Rides monitored",
    stat_safe:"Safe Score", stat_safe_sub:"Higher is better",
    stat_drowsy:"Drowsy Events", stat_drowsy_sub:"Total frames flagged",
    stat_total_frames:"Total Frames", stat_frames_sub:"Frames analyzed",
    recent_sessions:"Recent Sessions",
    th_date:"Date", th_vehicle:"Vehicle", th_frames:"Frames",
    th_drowsy:"Drowsy", th_score:"Score", th_duration:"Duration",
    th_avg_conf:"Avg Confidence",
    detection_title:"Live Detection",
    detection_sub:"Start a ride to begin real-time drowsiness monitoring",
    vehicle_select:"Select Vehicle", metrics_title:"Real-time Metrics",
    m_state:"State", m_cnn:"CNN Confidence",
    session_stats:"Session Stats", ss_frames:"Frames sent",
    ss_drowsy:"Drowsy frames", ss_duration:"Duration",
    btn_start:"🎥 Start Detection", btn_end:"🛑 End Ride",
    cam_placeholder:"Select a vehicle and click Start Detection",
    history_title:"Session History",
    history_sub:"All your recorded rides and drowsiness data",
    profile_title:"Account & Profile",
    profile_sub:"Manage your personal info and registered vehicles",
    personal_info:"Personal Info", full_name:"Full Name", email:"Email",
    language:"Preferred Language", save_changes:"Save Changes",
    my_vehicles:"My Vehicles", add_vehicle:"Add Vehicle",
    add_vehicle_btn:"+ Add Vehicle",
    v_name:"Name", v_type:"Type", v_plate:"License Plate",
    no_vehicles:"No vehicles added yet",
    no_sessions:"No sessions yet",
  },
  ta: {
    nav_main:"முக்கிய", nav_dashboard:"டாஷ்போர்டு", nav_live:"நேரடி கண்டறிதல்",
    nav_history:"அமர்வு வரலாறு", nav_account:"கணக்கு", nav_profile:"சுயவிவரம்",
    dashboard_title:"கண்ணோட்டம்", dashboard_sub:"உங்கள் தூக்க கண்டறிதல் செயல்பாடு",
    stat_sessions:"மொத்த அமர்வுகள்", stat_sessions_sub:"கண்காணிக்கப்பட்ட பயணங்கள்",
    stat_safe:"பாதுகாப்பு மதிப்பெண்", stat_safe_sub:"அதிகமானது நல்லது",
    stat_drowsy:"தூக்க நிகழ்வுகள்", stat_drowsy_sub:"கொடியிடப்பட்ட பிரேம்கள்",
    stat_total_frames:"மொத்த பிரேம்கள்", stat_frames_sub:"பகுப்பாய்வு செய்யப்பட்ட பிரேம்கள்",
    detection_title:"நேரடி கண்டறிதல்", btn_start:"🎥 தொடங்கு", btn_end:"🛑 பயணம் முடிக்கவும்",
    profile_title:"கணக்கு & சுயவிவரம்", full_name:"முழு பெயர்",
    email:"மின்னஞ்சல்", language:"விருப்பமான மொழி", save_changes:"சேமி",
    my_vehicles:"என் வாகனங்கள்", add_vehicle:"வாகனம் சேர்க்கவும்",
    add_vehicle_btn:"+ வாகனம் சேர்க்கவும்", v_name:"பெயர்", v_type:"வகை",
    v_plate:"பதிவு எண்", no_vehicles:"வாகனங்கள் இல்லை", no_sessions:"அமர்வுகள் இல்லை",
  },
  hi: {
    nav_main:"मुख्य", nav_dashboard:"डैशबोर्ड", nav_live:"लाइव डिटेक्शन",
    nav_history:"सत्र इतिहास", nav_account:"खाता", nav_profile:"प्रोफ़ाइल",
    dashboard_title:"अवलोकन", dashboard_sub:"आपकी नींद पहचान गतिविधि",
    detection_title:"लाइव डिटेक्शन", btn_start:"🎥 शुरू करें", btn_end:"🛑 सवारी समाप्त करें",
    profile_title:"खाता और प्रोफ़ाइल", full_name:"पूरा नाम",
    email:"ईमेल", language:"पसंदीदा भाषा", save_changes:"सहेजें",
    my_vehicles:"मेरे वाहन", add_vehicle:"वाहन जोड़ें",
    add_vehicle_btn:"+ वाहन जोड़ें", v_name:"नाम", v_type:"प्रकार",
    v_plate:"लाइसेंस प्लेट", no_vehicles:"कोई वाहन नहीं", no_sessions:"कोई सत्र नहीं",
  },
  ml: {
    nav_main:"പ്രധാനം", nav_dashboard:"ഡാഷ്ബോർഡ്", nav_live:"തൽസമയ കണ്ടെത്തൽ",
    nav_history:"സെഷൻ ചരിത്രം", nav_account:"അക്കൗണ്ട്", nav_profile:"പ്രൊഫൈൽ",
    dashboard_title:"അവലോകനം", dashboard_sub:"നിങ്ങളുടെ ഡ്രൗസിനെസ്സ് പ്രവർത്തനം",
    detection_title:"തൽസമയ കണ്ടെത്തൽ", btn_start:"🎥 ആരംഭിക്കുക", btn_end:"🛑 യാത്ര അവസാനിപ്പിക്കുക",
    profile_title:"അക്കൗണ്ടും പ്രൊഫൈലും", full_name:"പൂർണ്ണ പേര്",
    email:"ഇമെയിൽ", language:"ഭാഷ", save_changes:"സേവ് ചെയ്യുക",
    my_vehicles:"എന്റെ വാഹനങ്ങൾ", add_vehicle:"വാഹനം ചേർക്കുക",
    add_vehicle_btn:"+ വാഹനം ചേർക്കുക", v_name:"പേര്", v_type:"തരം",
    v_plate:"ലൈസൻസ് പ്ലേറ്റ്", no_vehicles:"വാഹനങ്ങൾ ഇല്ല", no_sessions:"സെഷനുകൾ ഇല്ല",
  },
  te: {
    nav_main:"ప్రధాన", nav_dashboard:"డాష్‌బోర్డ్", nav_live:"లైవ్ డిటెక్షన్",
    nav_history:"సెషన్ చరిత్ర", nav_account:"ఖాతా", nav_profile:"ప్రొఫైల్",
    dashboard_title:"అవలోకనం", detection_title:"లైవ్ డిటెక్షన్",
    btn_start:"🎥 ప్రారంభించు", btn_end:"🛑 రైడ్ ముగించు",
    profile_title:"ఖాతా & ప్రొఫైల్", full_name:"పూర్తి పేరు",
    email:"ఇమెయిల్", language:"భాష", save_changes:"సేవ్ చేయి",
    my_vehicles:"నా వాహనాలు", add_vehicle_btn:"+ వాహనం జోడించు",
    no_vehicles:"వాహనాలు లేవు", no_sessions:"సెషన్‌లు లేవు",
  },
  kn: {
    nav_main:"ಮುಖ್ಯ", nav_dashboard:"ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", nav_live:"ಲೈವ್ ಡಿಟೆಕ್ಷನ್",
    nav_history:"ಸೆಶನ್ ಇತಿಹಾಸ", nav_account:"ಖಾತೆ", nav_profile:"ಪ್ರೊಫೈಲ್",
    dashboard_title:"ಅವಲೋಕನ", detection_title:"ಲೈವ್ ಡಿಟೆಕ್ಷನ್",
    btn_start:"🎥 ಪ್ರಾರಂಭಿಸು", btn_end:"🛑 ರೈಡ್ ಮುಗಿಸು",
    profile_title:"ಖಾತೆ & ಪ್ರೊಫೈಲ್", full_name:"ಪೂರ್ಣ ಹೆಸರು",
    email:"ಇಮೇಲ್", language:"ಭಾಷೆ", save_changes:"ಉಳಿಸಿ",
    my_vehicles:"ನನ್ನ ವಾಹನಗಳು", add_vehicle_btn:"+ ವಾಹನ ಸೇರಿಸಿ",
    no_vehicles:"ವಾಹನಗಳಿಲ್ಲ", no_sessions:"ಸೆಶನ್‌ಗಳಿಲ್ಲ",
  },
  fr: {
    nav_dashboard:"Tableau de bord", nav_live:"Détection en direct",
    nav_history:"Historique", nav_profile:"Profil",
    dashboard_title:"Aperçu", detection_title:"Détection en direct",
    btn_start:"🎥 Démarrer", btn_end:"🛑 Terminer le trajet",
    profile_title:"Compte et Profil", full_name:"Nom complet",
    email:"E-mail", language:"Langue", save_changes:"Enregistrer",
    my_vehicles:"Mes Véhicules", add_vehicle_btn:"+ Ajouter véhicule",
    no_vehicles:"Aucun véhicule", no_sessions:"Aucune session",
  },
  de: {
    nav_dashboard:"Dashboard", nav_live:"Live-Erkennung",
    nav_history:"Verlauf", nav_profile:"Profil",
    dashboard_title:"Übersicht", detection_title:"Live-Erkennung",
    btn_start:"🎥 Starten", btn_end:"🛑 Fahrt beenden",
    profile_title:"Konto & Profil", full_name:"Vollständiger Name",
    email:"E-Mail", language:"Sprache", save_changes:"Speichern",
    my_vehicles:"Meine Fahrzeuge", add_vehicle_btn:"+ Fahrzeug hinzufügen",
    no_vehicles:"Keine Fahrzeuge", no_sessions:"Keine Sitzungen",
  },
  es: {
    nav_dashboard:"Panel", nav_live:"Detección en vivo",
    nav_history:"Historial", nav_profile:"Perfil",
    dashboard_title:"Resumen", detection_title:"Detección en vivo",
    btn_start:"🎥 Iniciar", btn_end:"🛑 Terminar viaje",
    profile_title:"Cuenta y Perfil", full_name:"Nombre completo",
    email:"Correo", language:"Idioma", save_changes:"Guardar",
    my_vehicles:"Mis Vehículos", add_vehicle_btn:"+ Agregar vehículo",
    no_vehicles:"Sin vehículos", no_sessions:"Sin sesiones",
  },
};

let lang = "en";
function applyLang(l) {
  lang = l;
  const t = { ...T.en, ...(T[l] || {}) };
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const k = el.getAttribute("data-i18n");
    if (t[k]) el.textContent = t[k];
  });
}
function i18n(k) { return (T[lang] && T[lang][k]) || (T.en[k]) || k; }

// ── Toast ───────────────────────────────────────────────────────────────────────
function toast(msg, type = "info") {
  const c = document.getElementById("toast-container");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── Page routing ─────────────────────────────────────────────────────────────────
function showPage(page) {
  document.querySelectorAll(".tab-page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById(`page-${page}`).classList.add("active");
  document.getElementById(`nav-${page}`).classList.add("active");
  if (page === "history")  loadHistory();
  if (page === "profile")  loadProfile();
  if (page === "dashboard") loadStats();
}

// ── API helpers ──────────────────────────────────────────────────────────────────
async function api(url, opts = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Request failed");
  return data;
}

// ── Logout ───────────────────────────────────────────────────────────────────────
async function handleLogout() {
  await fetch("/api/logout", { method: "POST" });
  window.location.href = "/auth";
}

// ── Load profile sidebar ─────────────────────────────────────────────────────────
async function loadSidebarUser() {
  try {
    const u = await api("/api/profile");
    document.getElementById("sidebar-name").textContent  = u.name;
    document.getElementById("sidebar-email").textContent = u.email;
    document.getElementById("user-avatar").textContent   = u.name[0].toUpperCase();
    // apply saved language
    if (u.language) applyLang(u.language);
  } catch {}
}

// ── Stats ────────────────────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const s = await api("/api/stats");
    document.getElementById("stat-sessions").textContent = s.total_sessions;
    document.getElementById("stat-safe").textContent     = s.safe_score + "%";
    document.getElementById("stat-drowsy").textContent   = s.total_drowsy_frames;
    document.getElementById("stat-frames").textContent   = s.total_frames;
  } catch {}

  try {
    const sessions = await api("/api/sessions");
    const tbody = document.getElementById("recent-tbody");
    if (!sessions.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted" style="padding:24px">${i18n('no_sessions')}</td></tr>`;
      return;
    }
    tbody.innerHTML = sessions.slice(0, 5).map(s => {
      const total  = s.total_frames || 0;
      const drowsy = s.drowsy_frames || 0;
      const score  = total ? Math.round((1 - drowsy / total) * 100) : 100;
      const cls    = score >= 90 ? "badge-good" : score >= 70 ? "badge-warn" : "badge-bad";
      return `<tr>
        <td>${fmtDate(s.start_time)}</td>
        <td>${s.vehicle_name || "—"}</td>
        <td>${total}</td>
        <td>${drowsy}</td>
        <td><span class="badge ${cls}">${score}%</span></td>
      </tr>`;
    }).join("");
  } catch {}
}

// ── History ──────────────────────────────────────────────────────────────────────
async function loadHistory() {
  const tbody = document.getElementById("history-tbody");
  tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding:32px">Loading…</td></tr>`;
  try {
    const sessions = await api("/api/sessions");
    if (!sessions.length) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding:32px">${i18n('no_sessions')}</td></tr>`;
      return;
    }
    tbody.innerHTML = sessions.map(s => {
      const total  = s.total_frames  || 0;
      const drowsy = s.drowsy_frames || 0;
      const score  = total ? Math.round((1 - drowsy / total) * 100) : 100;
      const cls    = score >= 90 ? "badge-good" : score >= 70 ? "badge-warn" : "badge-bad";
      const dur    = duration(s.start_time, s.end_time);
      return `<tr>
        <td>${fmtDate(s.start_time)}</td>
        <td>${s.vehicle_name ? `${vehicleIcon(s.vehicle_type)} ${s.vehicle_name}` : "—"}</td>
        <td>${dur}</td>
        <td>${total}</td>
        <td>${drowsy}</td>
        <td><span class="badge ${cls}">${score}%</span></td>
        <td>${((s.avg_confidence || 0) * 100).toFixed(1)}%</td>
      </tr>`;
    }).join("");
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding:32px">Error loading history</td></tr>`;
  }
}

// ── Profile ───────────────────────────────────────────────────────────────────────
async function loadProfile() {
  try {
    const u = await api("/api/profile");
    document.getElementById("p-name").value  = u.name;
    document.getElementById("p-email").value = u.email;
    document.getElementById("p-lang").value  = u.language || "en";
  } catch {}
  await loadVehicles();
}

async function saveProfile() {
  try {
    await api("/api/profile", {
      method: "PUT",
      body: JSON.stringify({
        name:     document.getElementById("p-name").value.trim(),
        language: document.getElementById("p-lang").value,
      }),
    });
    toast("Profile saved!", "success");
    applyLang(document.getElementById("p-lang").value);
    await loadSidebarUser();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ── Vehicles ───────────────────────────────────────────────────────────────────
async function loadVehicles() {
  const list = document.getElementById("vehicle-list");
  const detSel = document.getElementById("det-vehicle-select");
  try {
    const vehicles = await api("/api/vehicles");
    // sidebar vehicle list
    if (!vehicles.length) {
      list.innerHTML = `<div class="text-muted text-center" style="padding:12px">${i18n('no_vehicles')}</div>`;
    } else {
      list.innerHTML = vehicles.map(v => `
        <div class="vehicle-item" id="vi-${v.id}">
          <span class="vehicle-icon">${vehicleIcon(v.type)}</span>
          <div class="vehicle-info">
            <div class="vehicle-name">${v.name}</div>
            <div class="vehicle-meta">${v.type}${v.plate ? ' · ' + v.plate : ''}</div>
          </div>
          <button class="btn-icon btn-delete" onclick="deleteVehicle(${v.id})" title="Delete">🗑</button>
        </div>`).join("");
    }
    // detection tab dropdown
    const cur = detSel.value;
    detSel.innerHTML = `<option value="">— ${i18n('no_vehicles')} —</option>` +
      vehicles.map(v => `<option value="${v.id}">${vehicleIcon(v.type)} ${v.name}${v.plate ? ' (' + v.plate + ')' : ''}</option>`).join("");
    if (cur) detSel.value = cur;
  } catch {}
}

async function addVehicle() {
  const name  = document.getElementById("v-name").value.trim();
  const vtype = document.getElementById("v-type").value;
  const plate = document.getElementById("v-plate").value.trim();
  if (!name) { toast("Vehicle name is required", "error"); return; }
  try {
    await api("/api/vehicles", { method: "POST", body: JSON.stringify({ name, type: vtype, plate }) });
    document.getElementById("v-name").value  = "";
    document.getElementById("v-plate").value = "";
    toast("Vehicle added!", "success");
    await loadVehicles();
  } catch (e) { toast(e.message, "error"); }
}

async function deleteVehicle(id) {
  try {
    await api(`/api/vehicles/${id}`, { method: "DELETE" });
    toast("Vehicle removed", "info");
    await loadVehicles();
  } catch (e) { toast(e.message, "error"); }
}

// ── Browser Audio Alarm (Web Audio API) ──────────────────────────────────────────
let audioCtx = null;
let alarmInterval = null;
let isAlarmPlaying = false;

function initAudio() {
  if (!audioCtx) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    if (AudioContextClass) {
      audioCtx = new AudioContextClass();
    }
  }
  if (audioCtx && audioCtx.state === "suspended") {
    audioCtx.resume();
  }
}

function playSingleBeep(freq = 1300, duration = 0.25) {
  try {
    if (!audioCtx) initAudio();
    if (!audioCtx) return;

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = "sine";
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);

    gain.gain.setValueAtTime(0.3, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (err) {
    console.warn("Audio beep failed:", err);
  }
}

function startAlarmSound() {
  if (isAlarmPlaying) return;
  isAlarmPlaying = true;
  initAudio();
  playSingleBeep(1400, 0.28);
  alarmInterval = setInterval(() => {
    playSingleBeep(1400, 0.28);
  }, 450);
}

function stopAlarmSound() {
  if (!isAlarmPlaying) return;
  isAlarmPlaying = false;
  if (alarmInterval) {
    clearInterval(alarmInterval);
    alarmInterval = null;
  }
}

// ── Live Detection ────────────────────────────────────────────────────────────────
let stream        = null;
let detecting     = false;
let sessionId     = null;
let frameCount    = 0;
let drowsyCount   = 0;
let sessionStart  = null;
let durationTimer = null;
let lastFrameTime = performance.now();

const video   = () => document.getElementById("video-feed");
const canvas  = () => document.getElementById("capture-canvas");

async function startDetection() {
  initAudio();
  const vehicleId = document.getElementById("det-vehicle-select").value || null;

  // Start backend session
  try {
    const res = await api("/api/sessions/start", {
      method: "POST",
      body: JSON.stringify({ vehicle_id: vehicleId ? parseInt(vehicleId) : null }),
    });
    sessionId = res.session_id;
  } catch (e) { toast("Could not start session: " + e.message, "error"); return; }

  // Get camera
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
  } catch (e) { toast("Camera access denied: " + e.message, "error"); return; }

  const vid = video();
  vid.srcObject = stream;
  vid.style.display = "block";
  document.getElementById("video-placeholder").style.display = "none";
  document.getElementById("video-overlay").style.display     = "block";

  frameCount   = 0;
  drowsyCount  = 0;
  sessionStart = Date.now();
  detecting    = true;

  document.getElementById("btn-start").disabled = true;
  document.getElementById("btn-end").disabled   = false;

  // duration timer
  durationTimer = setInterval(() => {
    const elapsed = Math.floor((Date.now() - sessionStart) / 1000);
    const m = String(Math.floor(elapsed / 60)).padStart(2, "0");
    const s = String(elapsed % 60).padStart(2, "0");
    document.getElementById("ss-duration").textContent = `${m}:${s}`;
  }, 1000);

  detectLoop();
  toast("Detection started!", "success");
}

async function detectLoop() {
  if (!detecting) return;

  const vid = video();
  const cvs = canvas();
  if (vid.readyState >= 2) {
    cvs.width  = vid.videoWidth  || 320;
    cvs.height = vid.videoHeight || 240;
    const ctx = cvs.getContext("2d");
    ctx.drawImage(vid, 0, 0);
    const b64 = cvs.toDataURL("image/jpeg", 0.6);

    const now = performance.now();
    const fps = Math.round(1000 / (now - lastFrameTime));
    lastFrameTime = now;

    try {
      const r = await fetch("/api/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frame: b64, session_id: sessionId }),
      });
      const d = await r.json();
      updateMetrics(d, fps);
      frameCount++;
      if (d.state === "DROWSY") drowsyCount++;
      document.getElementById("ss-frames").textContent = frameCount;
      document.getElementById("ss-drowsy").textContent = drowsyCount;
    } catch {}
  }

  if (detecting) requestAnimationFrame(detectLoop);
}

function updateMetrics(d, fps) {
  const badge = document.getElementById("state-badge");
  const banner = document.getElementById("wake-banner");

  // clean up old state classes
  badge.className = "state-badge";
  const stateKey = (d.state || "NO FACE").replace(" ", "-");
  badge.classList.add(stateKey);
  badge.textContent = d.state || "NO FACE";

  if (d.state === "DROWSY") {
    banner.style.display = "block";
    startAlarmSound();
  } else {
    banner.style.display = "none";
    stopAlarmSound();
  }

  document.getElementById("m-state").textContent = d.state || "—";
  document.getElementById("m-ear").textContent   = d.face_detected ? d.ear.toFixed(3) : "—";
  document.getElementById("m-mar").textContent   = d.face_detected ? d.mar.toFixed(3) : "—";
  document.getElementById("m-cnn").textContent   = d.face_detected ? (d.cnn_confidence * 100).toFixed(1) + "%" : "—";
  document.getElementById("m-fps").textContent   = fps + " fps";

  // EAR bar: higher = more awake; threshold ≈ 0.21, normal ≈ 0.30
  const earPct = d.face_detected ? Math.min(d.ear / 0.35 * 100, 100) : 60;
  document.getElementById("ear-bar").style.width = earPct.toFixed(0) + "%";
  // MAR bar: higher = yawning
  const marPct = d.face_detected ? Math.min(d.mar / 1.0 * 100, 100) : 0;
  document.getElementById("mar-bar").style.width = marPct.toFixed(0) + "%";
}

async function endDetection() {
  detecting = false;
  stopAlarmSound();
  clearInterval(durationTimer);

  if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }

  const vid = video();
  vid.srcObject = null;
  vid.style.display = "none";
  document.getElementById("video-placeholder").style.display = "flex";
  document.getElementById("video-overlay").style.display     = "none";
  document.getElementById("wake-banner").style.display       = "none";

  document.getElementById("btn-start").disabled = false;
  document.getElementById("btn-end").disabled   = true;

  // End session on backend
  try {
    const res = await api("/api/sessions/end", { method: "POST" });
    toast(`Ride saved! ${res.drowsy_frames} drowsy frames out of ${res.total_frames}.`, "success");
  } catch (e) { toast("Error saving session: " + e.message, "error"); }

  await loadStats();
}

// ── Helpers ───────────────────────────────────────────────────────────────────────
function vehicleIcon(type) {
  const map = { Car:"🚗", Truck:"🚛", Bike:"🏍️", Bus:"🚌", Van:"🚐", Auto:"🛺" };
  return map[type] || "🚗";
}

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { month:"short", day:"numeric",
    hour:"2-digit", minute:"2-digit" });
}

function duration(start, end) {
  if (!start || !end) return "—";
  const s = Math.floor((new Date(end) - new Date(start)) / 1000);
  const m = Math.floor(s / 60), sec = s % 60;
  return `${m}m ${sec}s`;
}

// ── Init ──────────────────────────────────────────────────────────────────────────
(async () => {
  await loadSidebarUser();
  await loadStats();
  await loadVehicles();
})();
