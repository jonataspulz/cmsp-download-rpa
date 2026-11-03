"""
Automatically downloads the files (PDF, PPTX, PPT) of the "Materiais Digitais" SEDUC page
(https://repositorio.educacao.sp.gov.br/midia) for a list of school subjects 
("Componente Curricular").
"""

import locale
import os
import re
import subprocess
import sys
import time
import unicodedata
from itertools import product
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait


PAGE_URL = "https://repositorio.educacao.sp.gov.br/midia"


SCHOOL_YEAR = "2026"                       # page filter "Ano Letivo"
STAGE = "ENSINO MÉDIO"                     # page filter "Etapa"
GRADES = ["1ª SÉRIE"]                      # e.g. ["1ª SÉRIE", "2ª SÉRIE", "3ª SÉRIE"]
TERMS = ["1º SEMESTRE/1º BIMESTRE"]        # e.g. add "1º SEMESTRE/2º BIMESTRE", ...
SUBJECTS = [                               # your list of "Componente Curricular"
    "BIOLOGIA",
    "FÍSICA",
    "QUÍMICA",
]

WANTED_TYPES = {"PDF", "PPT", "PPTX"}

DEFAULT_TAB = "Materiais"

EXTRA_TABS = {
    "Acessibilidade Curricular": "Acessibilidade",
}


#   "auto" = follow the computer's regional settings;  or "en" / "pt".
UI_LANGUAGE = "auto"

OUTPUT_DIR = Path("downloads")
CHROME_PROFILE_DIR = Path("chrome_profile") 

DOWNLOAD_TIMEOUT = 90       # seconds to wait for each file to finish downloading
PAUSE_BETWEEN_CLICKS = 1.5  # seconds of breathing room between downloads (be kind to the server)

EQUIVALENT_EXTENSIONS = {
    "PPT": {".ppt", ".pptx"},
    "PPTX": {".pptx", ".ppt"},
    "PDF": {".pdf"},
}

SITE_FILE_LABEL = "Arquivo"

DEFAULT_LANGUAGE = "en"

MESSAGES = {
    "en": {
        "language.name": "English",
        "startup.language": "Interface language: {language} (set UI_LANGUAGE at the top of the file to change it)",
        "config.url_missing": "Edit PAGE_URL at the top of the file before running.",
        "config.empty": "The setting {name} is empty. Fill it in at the top of the file.",
        "config.not_text": "Filter '{select}': expected text, but got {kind} ({value}). "
                           "Check the settings at the top of the file.",
        "login.line1": ">>> Log in using the Chrome window that just opened.",
        "login.line2": ">>> When the page with the filters (School year, Stage...) is visible,",
        "login.prompt": ">>> come back here and press ENTER to start... ",
        "filters.option_not_found": "Option '{text}' not found in '{select}'.",
        "filters.skipping": "! {error}  -> skipping",
        "search.found": "Lessons found: {count}",
        "file.label": "File {number:02d} [{kind}]",
        "status.ok": "downloaded",
        "status.already_exists": "already downloaded",
        "status.ignored": "ignored (type not wanted)",
        "status.no_button": "button not found",
        "status.failed": "FAILED",
        "lesson.tab_no_files": "({tab}: no files)",
        "lesson.no_such_tab": "(this lesson has no '{tab}' tab)",
        "lesson.tab_no_effect": "! I clicked the '{tab}' tab, but the page did not change; skipping it",
        "lesson.tab_empty": "({tab}: tab opened, but it has no files)",
        "lesson.cannot_go_back": "! could not find the '{tab}' tab to go back to",
        "debug.saved": "(lesson HTML saved to {path} for troubleshooting)",
        "download.new_tab": "(opened a new browser tab: {url})",
        "summary.title": "=== SUMMARY ===",
        "summary.no_files": "Lessons with no files at all (in any tab):",
        "summary.no_extra_tab": "Lessons without the extra tab ({count}):",
        "summary.failed": "Files that failed (run the script again to retry only these):",
        "summary.output": "Files saved in: {path}",
    },
    "pt": {
        "language.name": "Português",
        "startup.language": "Idioma da interface: {language} (altere UI_LANGUAGE no começo do arquivo para trocar)",
        "config.url_missing": "Edite PAGE_URL no começo do arquivo antes de rodar.",
        "config.empty": "A configuração {name} está vazia. Preencha no começo do arquivo.",
        "config.not_text": "Filtro '{select}': esperava um texto, mas recebi {kind} ({value}). "
                           "Confira as configurações no começo do arquivo.",
        "login.line1": ">>> Faça o login na janela do Chrome que acabou de abrir.",
        "login.line2": ">>> Quando a página com os filtros (Ano Letivo, Etapa...) estiver visível,",
        "login.prompt": ">>> volte aqui e pressione ENTER para começar... ",
        "filters.option_not_found": "Opção '{text}' não encontrada em '{select}'.",
        "filters.skipping": "! {error}  -> pulando",
        "search.found": "Aulas encontradas: {count}",
        "file.label": "Arquivo {number:02d} [{kind}]",
        "status.ok": "baixado",
        "status.already_exists": "já baixado",
        "status.ignored": "ignorado (tipo não desejado)",
        "status.no_button": "botão não encontrado",
        "status.failed": "FALHOU",
        "lesson.tab_no_files": "({tab}: sem arquivos)",
        "lesson.no_such_tab": "(esta aula não tem a aba '{tab}')",
        "lesson.tab_no_effect": "! cliquei na aba '{tab}', mas a página não mudou; pulando",
        "lesson.tab_empty": "({tab}: aba aberta, mas sem arquivos)",
        "lesson.cannot_go_back": "! não achei a aba '{tab}' para voltar",
        "debug.saved": "(HTML desta aula salvo em {path} para diagnóstico)",
        "download.new_tab": "(abriu uma nova aba do navegador: {url})",
        "summary.title": "=== RESUMO ===",
        "summary.no_files": "Aulas sem nenhum arquivo (em nenhuma aba):",
        "summary.no_extra_tab": "Aulas sem a aba extra ({count}):",
        "summary.failed": "Arquivos que falharam (rode o script de novo para tentar apenas esses):",
        "summary.output": "Arquivos salvos em: {path}",
    },
}

_current_language = DEFAULT_LANGUAGE


def set_language(code: str) -> None:
    """Chooses the language used by t() from now on."""
    global _current_language
    _current_language = code if code in MESSAGES else DEFAULT_LANGUAGE


def t(key: str, **values) -> str:
    """
    Returns the message for 'key' in the current language, filling the {placeholders}.
    Falls back to English, and finally to the key itself, so it never crashes.
    """
    template = MESSAGES[_current_language].get(key) or MESSAGES[DEFAULT_LANGUAGE].get(key, key)
    return template.format(**values) if values else template


def say(key: str, indent: int = 0, **values) -> None:
    """print() for translated messages, with optional indentation."""
    print(" " * indent + t(key, **values))


# ---- Detecting the language from the computer's regional settings ----
# Each "source" returns a list of locale tags such as "pt_BR.UTF-8" or "en-US".
# Sources are tried in order; the FIRST one that knows the locale decides.
def _primary_subtag(tag: str) -> str:
    """'pt_BR.UTF-8' -> 'pt';  'en-US' -> 'en';  'C' / 'POSIX' / '' -> ''."""
    code = re.split(r"[_\-.@]", tag.strip(), maxsplit=1)[0].lower()
    return "" if code in ("c", "posix") else code


def _windows_locales() -> list:
    """Windows: the user's regional-format locale (Settings > Time & language > Region)."""
    if sys.platform != "win32":
        return []
    try:
        import ctypes

        buffer = ctypes.create_unicode_buffer(85)  # LOCALE_NAME_MAX_LENGTH
        if ctypes.windll.kernel32.GetUserDefaultLocaleName(buffer, len(buffer)):
            return [buffer.value]  # e.g. "pt-BR"
    except Exception:
        pass
    return []


def _posix_env_locales() -> list:
    """Linux/macOS: the same variables (and priority order) that gettext itself uses."""
    for variable in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(variable, "").strip()
        if value:
            return [part for part in value.split(":") if part]  # LANGUAGE may be "pt_BR:en"
    return []


def _macos_locales() -> list:
    """macOS: asks the system when the terminal did not export LANG (e.g. IDE launches)."""
    if sys.platform != "darwin":
        return []
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleLocale"], capture_output=True, text=True, timeout=3
        )
        return [result.stdout.strip()] if result.returncode == 0 and result.stdout.strip() else []
    except Exception:
        return []


def _python_locales() -> list:
    """Last resort: what Python itself believes the locale is."""
    try:
        return [locale.getlocale()[0] or ""]
    except Exception:
        return []


def detect_language(preference: str = "auto") -> str:
    """
    Returns a supported language code ("en", "pt"...).
    'preference' may force one ("pt"); "auto" follows the computer's regional settings.
    Unknown or unsupported languages fall back to English.
    """
    forced = _primary_subtag(preference or "")
    if forced in MESSAGES:
        return forced
    for source in (_windows_locales, _posix_env_locales, _macos_locales, _python_locales):
        subtags = [s for s in map(_primary_subtag, source()) if s]
        if subtags:
            return next((s for s in subtags if s in MESSAGES), DEFAULT_LANGUAGE)
    return DEFAULT_LANGUAGE


CARD_XPATH = (
    "//div[contains(concat(' ', normalize-space(@class), ' '), ' item ')]"
    "[.//span[contains(@class,'id-aula')]]"
)


JS_READ_CARD = """
const card = arguments[0];
const buttons = Array.from(card.querySelectorAll('button.btn-download'));
return {
  html: card.outerHTML,
  visible: buttons.map(b => !!(b.offsetWidth || b.offsetHeight || b.getClientRects().length)),
};
"""


def clean_filename(text: str, limit: int = 90) -> str:
    """Removes characters that are not allowed in file names and limits the length."""
    text = re.sub(r'[<>:"/\\|?*\n\r\t]', " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:limit].strip(" .")


def normalize_text(text: str) -> str:
    """'  Acessibilidade   CURRICULAR ' -> 'acessibilidade curricular' (no accents, lowercase)."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return " ".join(text.split()).casefold()


def as_list(value) -> list:
    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            result.extend(as_list(item))
        return result
    text = str(value).strip()
    return [text] if text else []


def detect_file_type(button) -> str:
    image = button.find("img", title=True)
    if image:
        found = re.search(r"documento\s+([A-Za-z0-9]+)", image["title"], re.I)  # site wording
        if found:
            return found.group(1).upper()
    text = re.sub(r"[^A-Za-z0-9]", "", button.get_text()).upper()
    return text or "UNKNOWN"


def detect_file_number(button, position: int) -> int:
    block = button.parent
    for _ in range(4):
        if block is None or len(block.select("button.btn-download")) > 1:
            break  # reached a block that mixes several buttons: the label is not this one's
        found = re.search(rf"{re.escape(SITE_FILE_LABEL)}\s*(\d+)", block.get_text(" "), re.I)
        if found:
            return int(found.group(1))
        block = block.parent
    return position


def parse_lesson_card(html: str, visible=None, label=None) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    id_tag = soup.select_one("span.id-aula strong")
    title_tag = soup.select_one("div.titulo-aula > span")
    lesson_id = re.sub(r"\D", "", id_tag.get_text()) if id_tag else ""  # "ID: 139302" -> "139302"
    title = " ".join(title_tag.get_text().split()) if title_tag else "untitled"

    files = []
    for k, button in enumerate(soup.select("button.btn-download")):
        if visible is not None and k not in visible:
            continue
        position = len(files) + 1
        files.append(
            {"k": k, "type": detect_file_type(button), "number": detect_file_number(button, position)}
        )

    # Final name of each file; if two are identical, append (2), (3)...
    middle = f" - {clean_filename(label)}" if label else ""
    repeats = {}
    for item in files:
        base = f"{clean_filename(title)} [ID {lesson_id}]{middle} - {SITE_FILE_LABEL} {item['number']:02d}"
        key = (base, item["type"])
        repeats[key] = repeats.get(key, 0) + 1
        if repeats[key] > 1:
            base += f" ({repeats[key]})"
        item["base_name"] = base

    return {"id": lesson_id, "title": title, "files": files}


def read_card(driver, card, label=None) -> dict:
    """Reads one card (a Selenium element): HTML + button visibility, in a single call."""
    data = driver.execute_script(JS_READ_CARD, card)
    visible = {k for k, v in enumerate(data["visible"]) if v}
    return parse_lesson_card(data["html"], visible, label)


def read_card_by_index(driver, card_index: int, label=None) -> dict:
    """Like read_card, but finds the card again by its number (the page may have redrawn)."""
    for _ in range(3):
        try:
            card = driver.find_elements(By.XPATH, CARD_XPATH)[card_index]
            return read_card(driver, card, label)
        except (StaleElementReferenceException, IndexError):
            time.sleep(0.4)
    return {"id": "", "title": "", "files": []}


def read_lessons(driver) -> list:
    lessons = []
    for card in driver.find_elements(By.XPATH, CARD_XPATH):
        try:
            lessons.append(read_card(driver, card))
        except StaleElementReferenceException:
            continue  # the page redrew itself mid-read; the next read will catch it
    return lessons


def create_browser() -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    #options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR.resolve()}")
    options.add_experimental_option(
        "prefs",
        {
            "download.prompt_for_download": False,         # do not ask where to save
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,    # PDFs download instead of opening in Chrome
            "profile.default_content_setting_values.automatic_downloads": 1,  # allow several downloads
        },
    )
    return webdriver.Chrome(options=options)


def set_download_folder(driver, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    try:
        driver.execute_cdp_cmd(
            "Browser.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(folder.resolve())},
        )
    except Exception:  # older Chrome versions
        driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(folder.resolve())},
        )


def select_option(driver, select_name: str, text: str, timeout: int = 20) -> None:
    if not isinstance(text, str):
        raise TypeError(
            t("config.not_text", select=select_name, kind=type(text).__name__, value=repr(text))
        )
    target = " ".join(text.split()).upper()

    def find_option(d):
        element = d.find_element(By.CSS_SELECTOR, f"select[name='{select_name}']")
        for option in element.find_elements(By.TAG_NAME, "option"):
            if " ".join(option.text.split()).upper() == target:
                return element, option.get_attribute("value")
        return False

    try:
        tolerant_wait = WebDriverWait(
            driver, timeout, ignored_exceptions=[StaleElementReferenceException]
        )
        element, value = tolerant_wait.until(find_option)
    except TimeoutException:
        raise ValueError(t("filters.option_not_found", text=text, select=select_name))
    Select(element).select_by_value(value)
    time.sleep(0.8)  # gives React time to update the following lists


def search_and_wait(driver) -> list:
    old_ids = [lesson["id"] for lesson in read_lessons(driver)]
    driver.find_element(By.ID, "botaoPesquisar").click()

    deadline = time.time() + 25
    while time.time() < deadline:
        time.sleep(1)
        lessons = read_lessons(driver)
        if [lesson["id"] for lesson in lessons] != old_ids:
            time.sleep(1)  # let it finish rendering
            return read_lessons(driver)
    return read_lessons(driver)  # nothing changed (or there are no results)


def locate_button(driver, card_index: int, k: int):
    cards = driver.find_elements(By.XPATH, CARD_XPATH)
    if card_index >= len(cards):
        return None
    buttons = cards[card_index].find_elements(By.CSS_SELECTOR, "button.btn-download")
    return buttons[k] if k < len(buttons) else None


def click(driver, element) -> None:
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
    time.sleep(0.3)
    try:
        element.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", element)


def find_tab(card, tab_title: str):
    target = normalize_text(tab_title)
    for element in card.find_elements(By.CSS_SELECTOR, "button, a, [role='tab']"):
        try:
            if "btn-download" in (element.get_attribute("class") or ""):
                continue  # download buttons are not tabs
            text = normalize_text(element.get_attribute("textContent") or "")
        except StaleElementReferenceException:
            continue
        # "Avaliar (Materiais)" does NOT match "Materiais": we compare the START of the text.
        if text == target or text.startswith(target):
            return element
    return None


def _card_html(driver, card_index: int) -> str:
    for _ in range(3):
        try:
            return driver.find_elements(By.XPATH, CARD_XPATH)[card_index].get_attribute("outerHTML")
        except (StaleElementReferenceException, IndexError):
            time.sleep(0.3)
    return ""


def open_tab(driver, card_index: int, tab_title: str, timeout: int = 10) -> str:
    cards = driver.find_elements(By.XPATH, CARD_XPATH)
    if card_index >= len(cards):
        return "no_tab"
    tab = find_tab(cards[card_index], tab_title)
    if tab is None:
        return "no_tab"

    before = _card_html(driver, card_index)
    click(driver, tab)

    # 1) wait for the card's HTML to change (the active tab changes style/content)
    current = before
    deadline = time.time() + timeout
    while time.time() < deadline and current == before:
        time.sleep(0.4)
        current = _card_html(driver, card_index)
    if current == before:
        return "no_effect"

    # 2) wait for the content to settle (in case the file list loads late)
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(0.7)
        newer = _card_html(driver, card_index)
        if newer == current:
            break
        current = newer
    return "ok"


def save_debug_html(driver, card_index: int, name: str) -> None:
    folder = OUTPUT_DIR / "_debug"
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / f"{clean_filename(name)}.html"
    file.write_text(_card_html(driver, card_index), encoding="utf-8")
    say("debug.saved", indent=6, path=file)


def already_downloaded(folder: Path, base_name: str, file_type: str) -> bool:
    extensions = EQUIVALENT_EXTENSIONS.get(file_type, {f".{file_type.lower()}"})
    return any((folder / f"{base_name}{ext}").exists() for ext in extensions)


def wait_for_download(folder: Path, before: set, timeout: int):
    deadline = time.time() + timeout
    while time.time() < deadline:
        now = set(os.listdir(folder))
        new = now - before
        partial = [f for f in now if f.endswith((".crdownload", ".tmp"))]
        complete = [f for f in new if not f.endswith((".crdownload", ".tmp"))]
        if complete and not partial:
            return folder / complete[0]
        time.sleep(0.5)
    return None


def download_from_url(driver, url: str, destination: Path) -> bool:
    if not url.startswith("http"):
        return False
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"], domain=cookie.get("domain"))
    response = session.get(url, timeout=60)
    if response.status_code != 200:
        return False
    destination.write_bytes(response.content)
    return True


def download_file(driver, card_index: int, file: dict, folder: Path) -> str:
    file_type, base_name = file["type"], file["base_name"]

    if already_downloaded(folder, base_name, file_type):
        return "already_exists"

    button = locate_button(driver, card_index, file["k"])
    if button is None:
        return "no_button"

    original_window = driver.current_window_handle
    windows_before = set(driver.window_handles)
    files_before = set(os.listdir(folder))

    click(driver, button)

    # Wait up to 6 s to find out what the click caused:
    # (a) a download started  or  (b) a new browser tab opened.
    start = time.time()
    while time.time() - start < 6:
        if set(os.listdir(folder)) - files_before or set(driver.window_handles) - windows_before:
            break
        time.sleep(0.3)

    downloaded = None
    new_windows = set(driver.window_handles) - windows_before
    if new_windows:
        # Case (b): a tab opened. It may start the download itself; if not, we use its URL.
        driver.switch_to.window(new_windows.pop())
        time.sleep(2)
        url = driver.current_url
        say("download.new_tab", indent=8, url=url[:100])
        downloaded = wait_for_download(folder, files_before, timeout=5)
        if downloaded is None:
            destination = folder / f"{base_name}.{file_type.lower()}"
            if download_from_url(driver, url, destination):
                downloaded = destination

    if downloaded is None:
        # Case (a): direct download; wait for it to finish.
        downloaded = wait_for_download(folder, files_before, timeout=DOWNLOAD_TIMEOUT)

    # Close any extra browser tabs and go back to the main one.
    for window in set(driver.window_handles) - {original_window}:
        driver.switch_to.window(window)
        driver.close()
    driver.switch_to.window(original_window)

    if downloaded is None:
        return "failed"

    # Rename to a readable name, keeping the real extension of the received file.
    extension = downloaded.suffix.lower() or f".{file_type.lower()}"
    final = folder / f"{base_name}{extension}"
    if downloaded != final:
        if final.exists():
            final.unlink()
        downloaded.rename(final)
    return "ok"


def new_summary() -> dict:
    return {
        "counts": {"ok": 0, "already_exists": 0, "ignored": 0, "no_button": 0, "failed": 0},
        "no_files": [],
        "no_extra_tab": [],
        "failures": [],
        "debug_done": set(),
    }


def describe_files(files: list) -> str:
    return ", ".join(t("file.label", number=f["number"], kind=f["type"]) for f in files)


def download_list(driver, card_index, files, folder, description, tab_label, summary) -> None:
    prefix = f"[{tab_label}] " if tab_label else ""
    for item in files:
        label = t("file.label", number=item["number"], kind=item["type"])
        if WANTED_TYPES is not None and item["type"] not in WANTED_TYPES:
            status = "ignored"
        else:
            status = download_file(driver, card_index, item, folder)
        summary["counts"][status] += 1
        print(f"      {prefix}{label}: {t('status.' + status)}")
        if status == "failed":
            summary["failures"].append(f"{description} - {prefix}{label}")
        if status == "ok":
            time.sleep(PAUSE_BETWEEN_CLICKS)


def process_lesson(driver, index, lesson, folder, subject, summary) -> None:
    description = f"{subject}: {lesson['title']}"
    print(f"  - {lesson['title'][:70]}  (ID {lesson['id']})")
    total_found = 0

    # ---- 1) default tab (Materiais): it was already read during the search ----
    if lesson["files"]:
        total_found += len(lesson["files"])
        print(f"      {DEFAULT_TAB}: {describe_files(lesson['files'])}")
        download_list(driver, index, lesson["files"], folder, description, None, summary)
    else:
        say("lesson.tab_no_files", indent=6, tab=DEFAULT_TAB)

    # ---- 2) extra tabs (e.g. Acessibilidade Curricular) ----
    for tab_title, tab_label in EXTRA_TABS.items():
        result = open_tab(driver, index, tab_title)

        if result == "no_tab":
            say("lesson.no_such_tab", indent=6, tab=tab_title)
            summary["no_extra_tab"].append(description)
            continue

        if result == "no_effect":
            say("lesson.tab_no_effect", indent=6, tab=tab_title)
            save_debug_html(driver, index, f"lesson_{lesson['id']}_{tab_label}_no_effect")
            continue

        extra = read_card_by_index(driver, index, tab_label)
        if extra["files"]:
            total_found += len(extra["files"])
            print(f"      {tab_title}: {describe_files(extra['files'])}")
            download_list(driver, index, extra["files"], folder, description, tab_label, summary)
        else:
            say("lesson.tab_empty", indent=6, tab=tab_title)
            if tab_label not in summary["debug_done"]:  # keep only the first case, for diagnosis
                summary["debug_done"].add(tab_label)
                save_debug_html(driver, index, f"lesson_{lesson['id']}_{tab_label}_empty")

        # go back to the default tab, leaving the lesson as we found it
        if open_tab(driver, index, DEFAULT_TAB) == "no_tab":
            say("lesson.cannot_go_back", indent=6, tab=DEFAULT_TAB)

    if total_found == 0:
        summary["no_files"].append(description)


def main():
    set_language(detect_language(UI_LANGUAGE))
    say("startup.language", language=t("language.name"))

    if "PASTE_THE_URL" in PAGE_URL:
        raise SystemExit(t("config.url_missing"))

    # Every filter accepts a text or a list; check that none of them ended up empty.
    years, stages = as_list(SCHOOL_YEAR), as_list(STAGE)
    grades, terms, subjects = as_list(GRADES), as_list(TERMS), as_list(SUBJECTS)
    for name, items in (("SCHOOL_YEAR", years), ("STAGE", stages), ("GRADES", grades),
                        ("TERMS", terms), ("SUBJECTS", subjects)):
        if not items:
            raise SystemExit(t("config.empty", name=name))

    driver = create_browser()
    driver.get(PAGE_URL)

    print()
    say("login.line1")
    say("login.line2")
    input(t("login.prompt"))

    summary = new_summary()

    for year, stage, grade, term, subject in product(years, stages, grades, terms, subjects):
        print(f"\n=== {year} | {stage} | {grade} | {term} | {subject} ===")
        try:
            # Order matters: each filter may change the options of the following ones.
            select_option(driver, "anoLetivo", year)
            select_option(driver, "etapa", stage)
            select_option(driver, "serieAno", grade)
            select_option(driver, "bimestre", term)
            select_option(driver, "componenteCurricular", subject)
        except ValueError as error:
            say("filters.skipping", indent=2, error=error)
            continue

        lessons = search_and_wait(driver)
        say("search.found", indent=2, count=len(lessons))
        if not lessons:
            continue

        levels = []
        if len(years) > 1:
            levels.append(year)       # year/stage folders only if you asked for more than one
        if len(stages) > 1:
            levels.append(stage)
        levels += [grade, term, subject]
        folder = OUTPUT_DIR.joinpath(*[clean_filename(level) for level in levels])
        set_download_folder(driver, folder)

        for index, lesson in enumerate(lessons):
            process_lesson(driver, index, lesson, folder, subject, summary)

    print()
    say("summary.title")
    for status, count in summary["counts"].items():
        print(f"  {t('status.' + status)}: {count}")
    if summary["no_files"]:
        print()
        say("summary.no_files")
        for item in summary["no_files"]:
            print(f"  - {item}")
    if summary["no_extra_tab"]:
        print()
        say("summary.no_extra_tab", count=len(summary["no_extra_tab"]))
        for item in summary["no_extra_tab"]:
            print(f"  - {item}")
    if summary["failures"]:
        print()
        say("summary.failed")
        for item in summary["failures"]:
            print(f"  - {item}")
    print()
    say("summary.output", path=OUTPUT_DIR.resolve())
    driver.quit()


if __name__ == "__main__":
    main()
