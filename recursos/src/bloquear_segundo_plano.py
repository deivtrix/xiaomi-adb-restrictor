import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import threading
import re
import time
import json
import html
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

# Helper to automatically download ADB from Google's servers if missing
def check_and_download_adb(project_root, adb_path, log_func):
    adb_dir = os.path.dirname(adb_path)
    if os.path.exists(adb_path):
        return True
        
    os.makedirs(adb_dir, exist_ok=True)
    log_func(">> [AVISO] ADB no encontrado. Descargando Android Platform Tools desde Google...")
    try:
        url = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"
        zip_file_path = os.path.join(project_root, "adb.zip")
        
        # Descarga
        urllib.request.urlretrieve(url, zip_file_path)
        log_func(">> Archivo descargado. Extrayendo herramientas...")
        
        # Extracción
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(project_root)
            
        # Mover archivos extraídos de 'platform-tools' a la carpeta 'adb'
        temp_dir = os.path.join(project_root, "platform-tools")
        if os.path.exists(temp_dir):
            for file_name in os.listdir(temp_dir):
                src_file = os.path.join(temp_dir, file_name)
                dest_file = os.path.join(adb_dir, file_name)
                if os.path.exists(dest_file):
                    os.remove(dest_file)
                os.rename(src_file, dest_file)
                
            # Limpiar temporales
            for file_name in os.listdir(temp_dir):
                try:
                    os.remove(os.path.join(temp_dir, file_name))
                except Exception:
                    pass
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass
                
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
            
        log_func(">> ADB instalado y configurado correctamente.")
        return True
    except Exception as e:
        log_func(f"! Error durante la instalacion automatica de ADB: {e}")
        return False

# Ajuste de rutas para ejecutarse desde la carpeta "src"
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SRC_DIR)
ADB = os.path.join(PROJECT_ROOT, "adb", "adb.exe")
DRIVERS_DIR = os.path.join(PROJECT_ROOT, "drivers")
CACHE_DIR = os.path.join(PROJECT_ROOT, "data")
CACHE_FILE = os.path.join(CACHE_DIR, "app_names_cache.json")

# Asegurar que el directorio de caché de datos exista
os.makedirs(CACHE_DIR, exist_ok=True)

# Intentar cargar caché local de nombres
try:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            app_cache = json.load(f)
    else:
        app_cache = {}
except Exception:
    app_cache = {}

def save_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(app_cache, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def adb_cmd(*args, timeout=20):
    try:
        r = subprocess.run([ADB] + list(args), capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    except Exception as e:
        return -1, str(e)

def get_clean_name_offline(pkg):
    mapping = {
        "com.whatsapp": "WhatsApp",
        "com.whatsapp.w4b": "WhatsApp Business",
        "org.telegram.messenger": "Telegram",
        "com.instagram.android": "Instagram",
        "com.spotify.music": "Spotify",
        "com.facebook.katana": "Facebook",
        "com.facebook.orca": "Messenger",
        "com.zhiliaoapp.musically": "TikTok",
        "com.waze": "Waze",
        "com.brave.browser": "Brave Browser",
        "com.habby.archero": "Archero",
        "com.openai.chatgpt": "ChatGPT",
        "com.deepseek.chat": "DeepSeek",
        "com.netflix.mediaclient": "Netflix",
        "com.microsoft.office.outlook": "Outlook",
        "com.yellowpepper.pichincha": "Banco Pichincha",
        "com.ubercab": "Uber",
        "com.ubercab.eats": "Uber Eats",
        "com.revolut.revolut": "Revolut",
        "com.github.android": "GitHub",
        "org.zwanoo.android.speedtest": "Speedtest",
        "com.deepl.mobiletranslator": "DeepL Translator",
        "com.amazon.mShop.android.shopping": "Amazon",
        "com.google.android.calendar": "Google Calendar",
        "com.ticktick.task": "TickTick",
        "com.twitter.android": "X (Twitter)",
        "com.supercell.clashofclans": "Clash of Clans",
        "com.kiloo.subwaysurf": "Subway Surfers",
        "com.adobe.lrmobile": "Lightroom",
        "com.x8bit.bitwarden": "Bitwarden",
        "com.canva.editor": "Canva",
        "us.zoom.videomeetings": "Zoom",
        "com.einnovation.temu": "Temu",
        "notion.id": "Notion",
        "org.videolan.vlc": "VLC",
        "com.activision.callofduty.shooter": "Call of Duty",
        "com.truecaller": "Truecaller",
        "com.appdeuna.wallet": "Deuna!",
    }
    if pkg in mapping:
        return mapping[pkg]
    
    parts = pkg.split('.')
    if len(parts) >= 2:
        last = parts[-1]
        generic = ["android", "app", "mobile", "client", "free", "browser", "messenger", "music"]
        if last.lower() in generic and len(parts) >= 3:
            name = parts[-2]
        else:
            name = last
        name = name.replace('_', ' ').replace('-', ' ')
        return name.title()
    return pkg


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ADB Background Restrictor Dashboard")
        self.root.geometry("980x780")
        self.root.minsize(850, 650)
        self.root.configure(bg="#F3F4F6")

        self.apps = []
        self.selected = set()
        self.app_widgets = {}
        self.powerkeeper_restricted = False
        self.screen_width = 1220
        self.screen_height = 2712
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_apps)
        self.executor = ThreadPoolExecutor(max_workers=5)

        self._build_ui()
        # Verificar y descargar ADB si falta en segundo plano para no congelar la UI
        threading.Thread(target=self._ensure_adb, daemon=True).start()

    def _build_hover(self, widget, normal_bg, hover_bg):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

    def _build_ui(self):
        # ─── Top bar (Header / Status) ───
        top_bar = tk.Frame(self.root, bg="#FFFFFF", height=60, highlightbackground="#E5E7EB", highlightthickness=1)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)

        # Connection status dot
        self.status_dot = tk.Canvas(top_bar, width=14, height=14, bg="#FFFFFF", highlightthickness=0)
        self.status_dot.pack(side=tk.LEFT, padx=(20, 10))
        self.dot = self.status_dot.create_oval(2, 2, 12, 12, fill="#757575", outline="")

        self.status_lbl = tk.Label(top_bar, text="Verificando...", font=("Segoe UI", 10, "bold"), fg="#4B5563", bg="#FFFFFF")
        self.status_lbl.pack(side=tk.LEFT)

        # Action buttons on header (with icons)
        self.driver_btn = tk.Button(top_bar, text="🔧 Instalar Drivers",
                                    font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg="#2563EB",
                                    activeforeground="#FFFFFF", activebackground="#1D4ED8",
                                    relief=tk.FLAT, padx=14, pady=5, cursor="hand2")
        self.driver_btn.pack(side=tk.RIGHT, padx=20)
        self.driver_btn.config(command=self._install_drivers)
        self._build_hover(self.driver_btn, "#2563EB", "#1D4ED8")

        self.pk_btn = tk.Button(top_bar, text="🛡️ PowerKeeper: Activo",
                                font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg="#4B5563",
                                activeforeground="#FFFFFF", activebackground="#374151",
                                relief=tk.FLAT, padx=14, pady=5, cursor="hand2")
        self.pk_btn.pack(side=tk.RIGHT)
        self.pk_btn.config(command=self._toggle_powerkeeper)
        self._build_hover(self.pk_btn, "#4B5563", "#374151")

        # ─── Subheader & Search Bar ───
        sub_bar = tk.Frame(self.root, bg="#F3F4F6")
        sub_bar.pack(fill=tk.X, padx=20, pady=(15, 5))

        # Title
        tk.Label(sub_bar, text="Aplicaciones de Terceros", font=("Segoe UI", 12, "bold"), fg="#1F2937", bg="#F3F4F6").pack(side=tk.LEFT)
        
        # Progress label
        self.progress_lbl = tk.Label(sub_bar, text="", font=("Segoe UI", 10, "bold"), fg="#059669", bg="#F3F4F6")
        self.progress_lbl.pack(side=tk.RIGHT)

        # Search Bar widget
        search_frame = tk.Frame(self.root, bg="#FFFFFF", highlightbackground="#E5E7EB", highlightthickness=1)
        search_frame.pack(fill=tk.X, padx=20, pady=(5, 5))

        tk.Label(search_frame, text="  🔍  ", font=("Segoe UI", 10), fg="#9CA3AF", bg="#FFFFFF").pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=("Segoe UI", 10),
                                     bg="#FFFFFF", fg="#1F2937", bd=0, insertbackground="black")
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=8)

        # ─── List Container (Scrollable) ───
        list_container = tk.Frame(self.root, bg="#F3F4F6")
        list_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Canvas & Scrollbar
        self.canvas = tk.Canvas(list_container, highlightthickness=0, bg="#F3F4F6")
        scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.canvas.yview)
        
        self.list_frame = tk.Frame(self.canvas, bg="#F3F4F6")
        self.list_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind Mousewheel globally
        self.root.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # ─── Control Bar (List actions) ───
        ctrl_bar = tk.Frame(self.root, bg="#F3F4F6")
        ctrl_bar.pack(fill=tk.X, padx=20, pady=(10, 5))

        # Select buttons helper
        def make_btn(text, cmd, bg_col, hover_col, side=tk.LEFT):
            btn = tk.Button(ctrl_bar, text=text, command=cmd, font=("Segoe UI", 9, "bold"),
                            fg="#374151", bg=bg_col, activeforeground="#1F2937", activebackground=hover_col,
                            relief=tk.FLAT, padx=12, pady=5, cursor="hand2")
            btn.pack(side=side, padx=4)
            self._build_hover(btn, bg_col, hover_col)
            return btn

        make_btn("⟳ Refrescar", self._refresh, "#E5E7EB", "#D1D5DB")
        make_btn("🔍 Leer Estados", self._read_all_states, "#E5E7EB", "#D1D5DB")
        make_btn("☑ Marcar Todo", self._select_all, "#E5E7EB", "#D1D5DB")
        make_btn("☒ Desmarcar", self._deselect_all, "#E5E7EB", "#D1D5DB")

        # ─── Panel de Acciones Rápidas (Agrupado) ───
        actions_panel = tk.LabelFrame(self.root, text=" ⚡ Acciones sobre seleccionadas ", font=("Segoe UI", 9, "bold"),
                                      bg="#F3F4F6", fg="#4B5563", highlightbackground="#E5E7EB", highlightthickness=1, bd=0, labelanchor="nw")
        actions_panel.pack(fill=tk.X, padx=20, pady=(5, 10), ipady=8)

        def make_action_btn(text, cmd, bg_col, hover_col):
            btn = tk.Button(actions_panel, text=text, command=cmd, font=("Segoe UI", 9, "bold"),
                            fg="#FFFFFF", bg=bg_col, activeforeground="#FFFFFF", activebackground=hover_col,
                            relief=tk.FLAT, padx=12, pady=6, cursor="hand2")
            btn.pack(side=tk.RIGHT, padx=6, pady=5)
            self._build_hover(btn, bg_col, hover_col)
            return btn

        make_action_btn("🔴 BLOQUEAR TODO", lambda: self._set_mode("deny"), "#DC2626", "#B91C1C")
        make_action_btn("🟣 RESTRINGIR 2° PLANO", lambda: self._set_mode("restricted"), "#7C3AED", "#6D28D9")
        make_action_btn("⏳ CERRAR TRAS 10 MIN", lambda: self._set_mode("working_set"), "#D97706", "#B45309")
        make_action_btn("🟢 SIN RESTRICCIONES", lambda: self._set_mode("active"), "#059669", "#047857")

        # ─── Console Logger ───
        logger_frame = tk.LabelFrame(self.root, text=" 📋 Consola de Eventos ", font=("Segoe UI", 9, "bold"),
                                     bg="#F3F4F6", fg="#4B5563", highlightbackground="#E5E7EB", highlightthickness=1, bd=0, labelanchor="nw")
        logger_frame.pack(fill=tk.BOTH, padx=20, pady=(0, 20))

        self.log = tk.Text(logger_frame, height=5, font=("Consolas", 9), bg="#FFFFFF",
                           fg="#0F766E", relief=tk.FLAT, insertbackground="black", borderwidth=8)
        self.log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._log(">> Sistema listo. Conecta tu celular para comenzar.")

    # ─── Helpers ───

    def _log(self, msg):
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.root.update_idletasks()

    def _set_status_text(self, text, color):
        self.status_lbl.config(text=text, fg=color)
        self.status_dot.itemconfig(self.dot, fill=color)

    def _get_device_status(self):
        _, out = adb_cmd("devices")
        if "\tdevice" in out:
            return "conectado"
        if "\tunauthorized" in out:
            return "no_autorizado"
        return "desconectado"

    def _get_screen_resolution(self):
        _, out = adb_cmd("shell", "wm size")
        m = re.search(r'(\d+)x(\d+)', out)
        if m:
            self.screen_width = int(m.group(1))
            self.screen_height = int(m.group(2))
            self._log(f">> Resolución detectada: {self.screen_width}x{self.screen_height}")

    # ─── Real App Label Resolution ───

    def _resolve_app_label_async(self, pkg):
        if pkg in app_cache:
            self._update_app_label_ui(pkg, app_cache[pkg])
            return

        try:
            url = f"https://play.google.com/store/apps/details?id={pkg}&hl=es"
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/100.0.0.0'}
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                html_data = response.read().decode('utf-8')
                m = re.search(r'<title[^>]*>(.*?)</title>', html_data)
                if m:
                    raw_title = m.group(1).strip()
                    title = raw_title.split(" - ")[0].strip()
                    title = html.unescape(title)
                    if title and "Google Play" not in title and "Error" not in title:
                        app_cache[pkg] = title
                        save_cache()
                        self._update_app_label_ui(pkg, title)
                        return
        except Exception:
            pass

    def _update_app_label_ui(self, pkg, clean_name):
        def run():
            if pkg in self.app_widgets:
                lbl = self.app_widgets[pkg]["lbl"]
                # Preservar el tachado si ya está completada
                current_font = lbl.cget("font")
                if "overstrike" in str(current_font):
                    lbl.config(text=f"{clean_name} ({pkg})", font=("Segoe UI", 9, "bold overstrike"))
                else:
                    lbl.config(text=f"{clean_name} ({pkg})")
                # Volver a filtrar si hay una búsqueda activa
                self._filter_apps()
        self.root.after(0, run)

    # ─── Read Standby Buckets from Device ───

    def _query_app_state(self, pkg):
        rc, out = adb_cmd("shell", f"am get-standby-bucket {pkg}")
        if rc == 0:
            try:
                return int(out.strip())
            except Exception:
                pass
        return -1

    def _update_app_status_ui(self, pkg, bucket):
        def run():
            if pkg in self.app_widgets:
                lbl_status = self.app_widgets[pkg]["lbl_status"]
                if bucket == 10:
                    lbl_status.config(text="Sin restricciones", fg="#059669")
                elif bucket == 20:
                    lbl_status.config(text="Cerrar tras 10 min", fg="#D97706")
                elif bucket == 45 or bucket == 40:
                    lbl_status.config(text="Restringir en segundo plano", fg="#7C3AED")
                elif bucket == -1:
                    lbl_status.config(text="Desconectado", fg="#DC2626")
                else:
                    lbl_status.config(text="Ahorro de batería (recomendado)", fg="#6B7280")
        self.root.after(0, run)

    def _read_all_states(self):
        status = self._get_device_status()
        if status != "conectado":
            self._log("! Conecta el dispositivo primero.")
            return

        def work():
            self._log(">> Consultando estado de batería de cada app en el dispositivo...")
            self.root.after(0, lambda: self.progress_lbl.config(text="Leyendo estados..."))
            
            # Consultas en paralelo para mayor velocidad
            futures = []
            for pkg in self.app_widgets.keys():
                futures.append((pkg, self.executor.submit(self._query_app_state, pkg)))
                
            for pkg, fut in futures:
                bucket = fut.result()
                self._update_app_status_ui(pkg, bucket)
                
            self.root.after(0, lambda: self.progress_lbl.config(text="Estados actualizados"))
            self._log(">> Lectura de estados completada.")

        threading.Thread(target=work, daemon=True).start()

    # ─── Filtering Apps ───

    def _filter_apps(self, *args):
        query = self.search_var.get().lower().strip()
        for pkg, widgets in self.app_widgets.items():
            friendly = app_cache.get(pkg, get_clean_name_offline(pkg)).lower()
            if not query or query in pkg.lower() or query in friendly:
                widgets["row"].pack(fill=tk.X, padx=10, pady=4)
            else:
                widgets["row"].pack_forget()

    # ─── Load & Render Apps ───

    def _load_all(self):
        def work():
            self._get_screen_resolution()
            _, out = adb_cmd("shell", "pm list packages -3")
            pkgs = []
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("package:"):
                    pkgs.append(line[8:])
            pkgs.sort()
            apps = [{"pkg": p} for p in pkgs]
            self.root.after(0, lambda: self._render_apps(apps))
            self.root.after(0, lambda: self._log(f">> OK: {len(apps)} aplicaciones encontradas."))

            # Lanzar resolución de nombres de Play Store
            for p in pkgs:
                self.executor.submit(self._resolve_app_label_async, p)
            
            # Consultar los estados de batería iniciales
            self._read_all_states()
                
        threading.Thread(target=work, daemon=True).start()

    def _refresh(self):
        status = self._get_device_status()
        if status != "conectado":
            self._log("! Conecta el dispositivo por USB e inicia la depuración.")
            return
        self._log(">> Cargando aplicaciones...")
        self._load_all()

    def _render_apps(self, apps):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.app_widgets.clear()
        self.selected.clear()
        self.apps = apps

        if not apps:
            tk.Label(self.list_frame, text="No se encontraron aplicaciones en el dispositivo.",
                     fg="#6B7280", bg="#F3F4F6", font=("Segoe UI", 10)).pack(pady=40)
            return

        for app in apps:
            pkg_id = app["pkg"]
            
            # Row container card (White background, light gray borders)
            row = tk.Frame(self.list_frame, bg="#FFFFFF", highlightbackground="#E5E7EB",
                           highlightthickness=1, pady=6)
            row.pack(fill=tk.X, padx=10, pady=4)

            # Custom Indicator Label (replacing Checkbutton)
            ind_lbl = tk.Label(row, text="○", font=("Segoe UI", 12), fg="#9CA3AF", bg="#FFFFFF")
            ind_lbl.pack(side=tk.LEFT, padx=(15, 10))

            # Settings button on the far right
            btn_settings = tk.Button(row, text="⚙️", font=("Segoe UI", 9),
                                     fg="#4B5563", bg="#FFFFFF", activeforeground="#1F2937",
                                     activebackground="#F3F4F6", relief=tk.FLAT, cursor="hand2",
                                     bd=0, padx=8, pady=2)
            btn_settings.pack(side=tk.RIGHT, padx=(0, 15))

            # Status Badge Label on the right
            lbl_status = tk.Label(row, text="Pendiente", font=("Segoe UI", 8, "bold"),
                                  fg="#6B7280", bg="#FFFFFF")
            lbl_status.pack(side=tk.RIGHT, padx=15)

            # Initial clean name offline
            friendly_name = get_clean_name_offline(pkg_id)
            txt = f"{friendly_name} ({pkg_id})" if friendly_name.lower() != pkg_id.lower() else pkg_id
            
            lbl = tk.Label(row, text=txt, anchor=tk.W, font=("Segoe UI", 9, "bold"),
                           fg="#1F2937", bg="#FFFFFF", cursor="hand2")
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

            # Hover animations
            def make_hover(r=row, ind=ind_lbl, l=lbl, s=lbl_status, b=btn_settings):
                def enter(e):
                    r.config(bg="#F9FAFB")
                    ind.config(bg="#F9FAFB")
                    l.config(bg="#F9FAFB")
                    s.config(bg="#F9FAFB")
                    b.config(bg="#F9FAFB")
                def leave(e):
                    r.config(bg="#FFFFFF")
                    ind.config(bg="#FFFFFF")
                    l.config(bg="#FFFFFF")
                    s.config(bg="#FFFFFF")
                    b.config(bg="#FFFFFF")
                r.bind("<Enter>", enter)
                r.bind("<Leave>", leave)
                l.bind("<Enter>", enter)
                l.bind("<Leave>", leave)
                ind.bind("<Enter>", enter)
                ind.bind("<Leave>", leave)
                s.bind("<Enter>", enter)
                s.bind("<Leave>", leave)
                b.bind("<Enter>", enter)
                b.bind("<Leave>", leave)
            make_hover()

            def toggle(e, p=pkg_id, ind=ind_lbl):
                if p in self.selected:
                    self.selected.discard(p)
                    ind.config(text="○", fg="#9CA3AF")
                else:
                    self.selected.add(p)
                    ind.config(text="●", fg="#10B981")

            def open_single_settings(e=None, p=pkg_id):
                friendly = app_cache.get(p, get_clean_name_offline(p))
                self._log(f">> Abriendo ajustes de batería para: {friendly}")
                threading.Thread(target=lambda: adb_cmd("shell", f"am start -n \"com.miui.securitycenter/com.miui.powercenter.legacypowerrank.PowerDetailActivity\" --es package_name \"{p}\""), daemon=True).start()

            btn_settings.config(command=open_single_settings)

            lbl.bind("<Button-1>", toggle)
            row.bind("<Button-1>", toggle)
            ind_lbl.bind("<Button-1>", toggle)

            # Double click actions
            lbl.bind("<Double-Button-1>", open_single_settings)
            row.bind("<Double-Button-1>", open_single_settings)
            ind_lbl.bind("<Double-Button-1>", open_single_settings)
            lbl_status.bind("<Double-Button-1>", open_single_settings)

            self.app_widgets[pkg_id] = {"row": row, "indicator": ind_lbl, "lbl": lbl, "lbl_status": lbl_status, "btn_settings": btn_settings}

        # Aplicar filtro si ya hay texto en la búsqueda
        self._filter_apps()

    # ─── Ultra-Fast Coordinate Tapping Mode ───

    def _set_mode(self, mode):
        status = self._get_device_status()
        if status != "conectado":
            self._log("! Dispositivo no conectado.")
            return

        selected = [p for p in self.selected if p in self.app_widgets]
        if not selected:
            self._log("! Selecciona al menos una aplicación.")
            return

        # Ordenar el procesamiento según el orden exacto en el que aparecen en la lista (arriba a abajo)
        pkg_order = {app["pkg"]: idx for idx, app in enumerate(self.apps)}
        selected = sorted(selected, key=lambda p: pkg_order.get(p, 9999))

        # Limpiar marcas previas de completado para las apps seleccionadas
        for pkg in selected:
            if pkg in self.app_widgets:
                self.app_widgets[pkg]["lbl"].config(font=("Segoe UI", 9, "bold"), fg="#1F2937")
                self.app_widgets[pkg]["row"].config(bg="#FFFFFF")
                self.app_widgets[pkg]["indicator"].config(text="●", fg="#10B981")

        y_ratios = {
            "active": 0.36,         # "Sin restricciones"
            "working_set": 0.612,   # "Cerrar aplicaciones después de 10 min..."
            "restricted": 0.69,     # "Restringir aplicaciones en segundo plano"
            "deny": 0.69            # "Restringir aplicaciones en segundo plano"
        }
        y_ratio = y_ratios.get(mode, 0.612)
        
        mode_name_es = {
            "active": "Sin restricciones",
            "working_set": "Cerrar tras 10 min",
            "restricted": "Restringir segundo plano",
            "deny": "Bloquear todo"
        }.get(mode, mode)

        def work():
            self.root.after(0, lambda: self.progress_lbl.config(text=f"Procesando: 0 de {len(selected)}"))
            self._log("==================================================")
            self._log(f"▶ INICIANDO PROCESAMIENTO ({len(selected)} apps) — Modo: {mode_name_es}")
            self._log("==================================================")
            
            for idx, pkg in enumerate(selected):
                friendly = app_cache.get(pkg, get_clean_name_offline(pkg))
                self._log(f"⏳ [{idx+1}/{len(selected)}] Configurando: {friendly}...")

                # 1. Comandos AOSP rápidos en segundo plano
                aosp_cmds = []
                if mode == "deny":
                    aosp_cmds = [
                        f"cmd appops set {pkg} RUN_ANY_IN_BACKGROUND ignore",
                        f"cmd appops set {pkg} RUN_IN_BACKGROUND ignore",
                        f"am set-standby-bucket {pkg} restricted",
                    ]
                elif mode == "restricted":
                    aosp_cmds = [
                        f"cmd appops set {pkg} RUN_ANY_IN_BACKGROUND ignore",
                        f"cmd appops set {pkg} RUN_IN_BACKGROUND ignore",
                        f"am set-standby-bucket {pkg} restricted",
                    ]
                elif mode == "working_set":
                    aosp_cmds = [
                        f"cmd appops set {pkg} RUN_ANY_IN_BACKGROUND allow",
                        f"cmd appops set {pkg} RUN_IN_BACKGROUND allow",
                        f"am set-standby-bucket {pkg} working_set",
                    ]
                else:
                    aosp_cmds = [
                        f"cmd appops set {pkg} RUN_ANY_IN_BACKGROUND allow",
                        f"cmd appops set {pkg} RUN_IN_BACKGROUND allow",
                        f"am set-standby-bucket {pkg} active",
                    ]

                for cmd in aosp_cmds:
                    adb_cmd("shell", cmd)

                # 2. Cierre forzado rápido para ventana limpia
                adb_cmd("shell", "am force-stop com.miui.securitycenter")
                
                # 3. Lanzar pantalla de detalles de batería
                adb_cmd("shell", f"am start -n \"com.miui.securitycenter/com.miui.powercenter.legacypowerrank.PowerDetailActivity\" --es package_name \"{pkg}\"")
                
                # Espera óptima para carga de página
                time.sleep(0.5)

                # 4. Tocar opción deseada
                cx = int(self.screen_width * 0.5)
                cy = int(self.screen_height * y_ratio)
                adb_cmd("shell", f"input tap {cx} {cy}")

                # 5. Tocar botón "Aceptar" SOLO si es el modo restringido (que abre el diálogo de advertencia)
                if mode in ["restricted", "deny"]:
                    # Espera óptima para cuadro de diálogo Aceptar
                    time.sleep(0.35)
                    ax = int(self.screen_width * 0.75)
                    ay = int(self.screen_height * 0.79)
                    adb_cmd("shell", f"input tap {ax} {ay}")

                time.sleep(0.15)
                
                # Marcar app como completada en la UI
                self.root.after(0, lambda p=pkg, i=idx+1, t=len(selected): self._mark_app_completed(p, i, t))
                self._log(f"   ✔ {friendly} configurado con éxito")

            # Cerrar al finalizar todo
            adb_cmd("shell", "am force-stop com.miui.securitycenter")
            self._log("==================================================")
            self._log("✔ ¡PROCESO COMPLETADO! Todas las apps configuradas.")
            self._log("==================================================")
            
            # Recargar estados finales automáticamente
            self._read_all_states()

        threading.Thread(target=work, daemon=True).start()

    def _mark_app_completed(self, pkg, current, total):
        self.progress_lbl.config(text=f"Procesando: {current} de {total}")
        if pkg in self.app_widgets:
            widgets = self.app_widgets[pkg]
            widgets["lbl"].config(font=("Segoe UI", 9, "bold overstrike"), fg="#9CA3AF")
            widgets["indicator"].config(text="✓", fg="#10B981")
            widgets["row"].config(bg="#F9FAFB")
            self.selected.discard(pkg)

    # ─── PowerKeeper toggle ───

    def _toggle_powerkeeper(self):
        status = self._get_device_status()
        if status != "conectado":
            self._log("! Conecta el dispositivo primero.")
            return

        def work():
            pk = "com.miui.powerkeeper"
            ops = ["WRITE_SETTINGS", "GET_USAGE_STATS", "RUN_IN_BACKGROUND",
                   "RUN_ANY_IN_BACKGROUND", "START_FOREGROUND"]
            mode = "allow" if self.powerkeeper_restricted else "deny"
            label = "restaurado (Activo)" if self.powerkeeper_restricted else "restringido (Inactivo)"
            
            for op in ops:
                adb_cmd("shell", f"cmd appops set {pk} {op} {mode}")

            self.powerkeeper_restricted = not self.powerkeeper_restricted
            if self.powerkeeper_restricted:
                self.root.after(0, lambda: self.pk_btn.config(text="🛡️ PowerKeeper: Inactivo", bg="#DC2626"))
            else:
                self.root.after(0, lambda: self.pk_btn.config(text="🛡️ PowerKeeper: Activo", bg="#4B5563"))
            self._log(f">> PowerKeeper ha sido {label}.")

        threading.Thread(target=work, daemon=True).start()

    # ─── Install drivers ───

    def _install_drivers(self):
        mtk = os.path.join(DRIVERS_DIR, "mtk_driver", "MTK_USB_All_v1.0.8", "MTK_USB_All_v1.0.8.exe")
        if os.path.exists(mtk):
            os.startfile(mtk)
        ggl = os.path.join(DRIVERS_DIR, "google_usb_driver", "usb_driver")
        if os.path.exists(ggl):
            os.startfile(ggl)
        self._log(">> Iniciando instaladores de drivers MediaTek / ADB...")

    def _ensure_adb(self):
        if os.path.exists(ADB):
            self._update_status_loop()
            return
            
        self.root.after(0, lambda: self._set_status_text("INSTALANDO ADB...", "#D97706"))
        self._log(">> [AVISO] ADB.exe no encontrado en recursos/adb/")
        
        success = check_and_download_adb(PROJECT_ROOT, ADB, self._log)
        if success:
            self._log(">> ADB listo. Iniciando bucle de conexion.")
            self._update_status_loop()
        else:
            self.root.after(0, lambda: self._set_status_text("ERROR ADB", "#DC2626"))
            self.root.after(0, lambda: messagebox.showerror(
                "Error de ADB", 
                "No se encontro ADB y fallo la descarga automatica.\n"
                "Asegurate de tener conexion a Internet o conserva la carpeta 'recursos/adb' intacta."
            ))

    # ─── Status auto-update loop ───

    def _update_status_loop(self):
        status = self._get_device_status()
        if status == "conectado":
            self._set_status_text("CONECTADO", "#059669")
            if not self.apps:
                self._refresh()
        elif status == "no_autorizado":
            self._set_status_text("NO AUTORIZADO - Acepta en tu celular", "#D97706")
        else:
            self._set_status_text("DESCONECTADO - Conecta por USB", "#DC2626")
        self.root.after(3000, self._update_status_loop)

    def _select_all(self):
        for pkg, w in self.app_widgets.items():
            self.selected.add(pkg)
            w["indicator"].config(text="●", fg="#10B981")

    def _deselect_all(self):
        for pkg, w in self.app_widgets.items():
            w["indicator"].config(text="○", fg="#9CA3AF")
        self.selected.clear()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
