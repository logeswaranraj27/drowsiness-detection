/* auth.js — handles login/signup page logic */

// ── i18n translations ──────────────────────────────────────────────────────────
const TRANSLATIONS = {
  en: {
    auth_title_login:  "Welcome back",
    auth_sub_login:    "Sign in to your account to continue",
    auth_title_signup: "Create account",
    auth_sub_signup:   "Join DrowsyGuard and stay safe on the road",
    login:             "Sign In",
    signup:            "Create Account",
    email:             "Email",
    password:          "Password",
    full_name:         "Full Name",
    confirm_password:  "Confirm Password",
    language:          "Preferred Language",
    sign_in:           "Sign In",
    create_account:    "Create Account",
  },
  ta: {
    auth_title_login:  "மீண்டும் வரவேற்கிறோம்",
    auth_sub_login:    "தொடர உங்கள் கணக்கில் உள்நுழையவும்",
    auth_title_signup: "கணக்கு உருவாக்கவும்",
    auth_sub_signup:   "DrowsyGuard-ல் சேரவும்",
    login:             "உள்நுழைய",
    signup:            "கணக்கு உருவாக்கு",
    email:             "மின்னஞ்சல்",
    password:          "கடவுச்சொல்",
    full_name:         "முழு பெயர்",
    confirm_password:  "கடவுச்சொல் உறுதிப்படுத்து",
    language:          "விருப்பமான மொழி",
    sign_in:           "உள்நுழைய",
    create_account:    "கணக்கு உருவாக்கு",
  },
  hi: {
    auth_title_login:  "वापस स्वागत है",
    auth_sub_login:    "जारी रखने के लिए साइन इन करें",
    auth_title_signup: "खाता बनाएं",
    auth_sub_signup:   "DrowsyGuard से जुड़ें",
    login:             "साइन इन",
    signup:            "खाता बनाएं",
    email:             "ईमेल",
    password:          "पासवर्ड",
    full_name:         "पूरा नाम",
    confirm_password:  "पासवर्ड की पुष्टि करें",
    language:          "पसंदीदा भाषा",
    sign_in:           "साइन इन",
    create_account:    "खाता बनाएं",
  },
  ml: {
    auth_title_login:  "തിരിച്ചു സ്വാഗതം",
    auth_sub_login:    "തുടരാൻ ലോഗിൻ ചെയ്യുക",
    auth_title_signup: "അക്കൗണ്ട് ഉണ്ടാക്കുക",
    auth_sub_signup:   "DrowsyGuard-ൽ ചേരുക",
    login:             "ലോഗിൻ",
    signup:            "അക്കൗണ്ട് ഉണ്ടാക്കുക",
    email:             "ഇമെയിൽ",
    password:          "പാസ്‌വേഡ്",
    full_name:         "മുഴുവൻ പേര്",
    confirm_password:  "പാസ്‌വേഡ് സ്ഥിരീകരിക്കുക",
    language:          "ഭാഷ",
    sign_in:           "ലോഗിൻ",
    create_account:    "അക്കൗണ്ട് ഉണ്ടാക്കുക",
  },
  te: {
    auth_title_login:  "తిరిగి స్వాగతం",
    auth_sub_login:    "కొనసాగించడానికి సైన్ ఇన్ చేయండి",
    auth_title_signup: "ఖాతా సృష్టించండి",
    auth_sub_signup:   "DrowsyGuard లో చేరండి",
    login:             "సైన్ ఇన్",
    signup:            "ఖాతా సృష్టించు",
    email:             "ఇమెయిల్",
    password:          "పాస్‌వర్డ్",
    full_name:         "పూర్తి పేరు",
    confirm_password:  "పాస్‌వర్డ్ నిర్ధారించండి",
    language:          "భాష",
    sign_in:           "సైన్ ఇన్",
    create_account:    "ఖాతా సృష్టించు",
  },
  kn: {
    auth_title_login:  "ಮತ್ತೆ ಸ್ವಾಗತ",
    auth_sub_login:    "ಮುಂದುವರಿಯಲು ಸೈನ್ ಇನ್ ಮಾಡಿ",
    auth_title_signup: "ಖಾತೆ ರಚಿಸಿ",
    auth_sub_signup:   "DrowsyGuard ಗೆ ಸೇರಿ",
    login:             "ಸೈನ್ ಇನ್",
    signup:            "ಖಾತೆ ರಚಿಸಿ",
    email:             "ಇಮೇಲ್",
    password:          "ಪಾಸ್ವರ್ಡ್",
    full_name:         "ಪೂರ್ಣ ಹೆಸರು",
    confirm_password:  "ಪಾಸ್ವರ್ಡ್ ದೃಢೀಕರಿಸಿ",
    language:          "ಭಾಷೆ",
    sign_in:           "ಸೈನ್ ಇನ್",
    create_account:    "ಖಾತೆ ರಚಿಸಿ",
  },
  fr: {
    auth_title_login:  "Bon retour",
    auth_sub_login:    "Connectez-vous pour continuer",
    auth_title_signup: "Créer un compte",
    auth_sub_signup:   "Rejoignez DrowsyGuard",
    login:             "Se connecter",
    signup:            "Créer un compte",
    email:             "E-mail",
    password:          "Mot de passe",
    full_name:         "Nom complet",
    confirm_password:  "Confirmer le mot de passe",
    language:          "Langue préférée",
    sign_in:           "Se connecter",
    create_account:    "Créer un compte",
  },
  de: {
    auth_title_login:  "Willkommen zurück",
    auth_sub_login:    "Melden Sie sich an, um fortzufahren",
    auth_title_signup: "Konto erstellen",
    auth_sub_signup:   "Treten Sie DrowsyGuard bei",
    login:             "Anmelden",
    signup:            "Konto erstellen",
    email:             "E-Mail",
    password:          "Passwort",
    full_name:         "Vollständiger Name",
    confirm_password:  "Passwort bestätigen",
    language:          "Bevorzugte Sprache",
    sign_in:           "Anmelden",
    create_account:    "Konto erstellen",
  },
  es: {
    auth_title_login:  "Bienvenido de nuevo",
    auth_sub_login:    "Inicia sesión para continuar",
    auth_title_signup: "Crear cuenta",
    auth_sub_signup:   "Únete a DrowsyGuard",
    login:             "Iniciar sesión",
    signup:            "Crear cuenta",
    email:             "Correo electrónico",
    password:          "Contraseña",
    full_name:         "Nombre completo",
    confirm_password:  "Confirmar contraseña",
    language:          "Idioma preferido",
    sign_in:           "Iniciar sesión",
    create_account:    "Crear cuenta",
  },
};

let currentLang = "en";
let currentTab  = "login";

// ── Language ────────────────────────────────────────────────────────────────────
function applyLang(lang) {
  currentLang = lang;
  const t = TRANSLATIONS[lang] || TRANSLATIONS.en;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (t[key]) el.textContent = t[key];
  });
  // update dynamic title/sub
  if (currentTab === "login") {
    document.getElementById("auth-title").textContent = t.auth_title_login;
    document.getElementById("auth-sub").textContent   = t.auth_sub_login;
  } else {
    document.getElementById("auth-title").textContent = t.auth_title_signup;
    document.getElementById("auth-sub").textContent   = t.auth_sub_signup;
  }
  // sync signup lang select
  const sl = document.getElementById("signup-lang");
  if (sl) sl.value = lang;
}

// ── Tab switching ───────────────────────────────────────────────────────────────
function switchTab(tab) {
  currentTab = tab;
  const t = TRANSLATIONS[currentLang] || TRANSLATIONS.en;

  document.getElementById("tab-login").classList.toggle("active",  tab === "login");
  document.getElementById("tab-signup").classList.toggle("active", tab === "signup");
  document.getElementById("login-form").style.display  = tab === "login"  ? "" : "none";
  document.getElementById("signup-form").style.display = tab === "signup" ? "" : "none";
  document.getElementById("login-error").textContent  = "";
  document.getElementById("signup-error").textContent = "";

  if (tab === "login") {
    document.getElementById("auth-title").textContent = t.auth_title_login  || "Welcome back";
    document.getElementById("auth-sub").textContent   = t.auth_sub_login    || "Sign in to your account";
  } else {
    document.getElementById("auth-title").textContent = t.auth_title_signup || "Create account";
    document.getElementById("auth-sub").textContent   = t.auth_sub_signup   || "Join DrowsyGuard";
  }
}

// ── Login ───────────────────────────────────────────────────────────────────────
async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById("login-btn");
  const err = document.getElementById("login-error");
  err.textContent = "";
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Signing in…';

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email:    document.getElementById("login-email").value.trim(),
        password: document.getElementById("login-password").value,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");
    window.location.href = "/dashboard";
  } catch (ex) {
    err.textContent = ex.message;
    btn.disabled = false;
    btn.textContent = (TRANSLATIONS[currentLang] || TRANSLATIONS.en).sign_in || "Sign In";
  }
}

// ── Signup ──────────────────────────────────────────────────────────────────────
async function handleSignup(e) {
  e.preventDefault();
  const btn = document.getElementById("signup-btn");
  const err = document.getElementById("signup-error");
  err.textContent = "";

  const name     = document.getElementById("signup-name").value.trim();
  const email    = document.getElementById("signup-email").value.trim();
  const password = document.getElementById("signup-password").value;
  const confirm  = document.getElementById("signup-confirm").value;
  const lang     = document.getElementById("signup-lang").value;

  if (password !== confirm) {
    err.textContent = "Passwords do not match.";
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Creating account…';

  try {
    const res = await fetch("/api/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, language: lang }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Signup failed");
    window.location.href = "/dashboard";
  } catch (ex) {
    err.textContent = ex.message;
    btn.disabled = false;
    btn.textContent = (TRANSLATIONS[currentLang] || TRANSLATIONS.en).create_account || "Create Account";
  }
}

// ── Init ────────────────────────────────────────────────────────────────────────
// detect browser language and pre-select
(function () {
  const bl = (navigator.language || "en").substring(0, 2).toLowerCase();
  const supported = Object.keys(TRANSLATIONS);
  const sel = document.getElementById("lang-select");
  if (supported.includes(bl)) {
    sel.value = bl;
    applyLang(bl);
  }
})();
