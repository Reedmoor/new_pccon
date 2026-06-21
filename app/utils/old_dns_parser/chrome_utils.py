"""Определение версии Chrome и создание undetected-chromedriver."""
import logging
import os
import re
import shutil
import subprocess

logger = logging.getLogger(__name__)


def get_chrome_major_version():
    """Мажорная версия установленного Chrome или None для автоопределения uc."""
    env = os.environ.get("DNS_UC_VERSION_MAIN", "").strip()
    if env.isdigit():
        return int(env)

    try:
        import winreg

        reg_paths = (
            (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon"),
        )
        for hive, path in reg_paths:
            try:
                with winreg.OpenKey(hive, path) as key:
                    version, _ = winreg.QueryValueEx(key, "version")
                    major = int(str(version).split(".", 1)[0])
                    logger.info("Chrome %s (major %s) from registry", version, major)
                    return major
            except OSError:
                continue
    except ImportError:
        pass

    candidates = []
    for name in ("chrome", "google-chrome", "chromium"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    candidates.extend([
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ])

    seen = set()
    for exe in candidates:
        if not exe or exe in seen or not os.path.isfile(exe):
            continue
        seen.add(exe)
        try:
            out = subprocess.check_output(
                [exe, "--version"],
                stderr=subprocess.STDOUT,
                text=True,
                timeout=15,
            )
            match = re.search(r"(\d+)\.", out)
            if match:
                major = int(match.group(1))
                logger.info("Chrome major %s from %s (%s)", major, exe, out.strip())
                return major
        except Exception as exc:
            logger.debug("Chrome version check failed for %s: %s", exe, exc)

    logger.warning("Chrome version not detected, undetected-chromedriver will auto-detect")
    return None


def create_uc_driver(**kwargs):
    """Создаёт uc.Chrome с driver под текущую версию браузера."""
    import undetected_chromedriver as uc

    version = get_chrome_major_version()
    if version is not None and "version_main" not in kwargs:
        kwargs["version_main"] = version
        logger.info("ChromeDriver version_main=%s", version)
    return uc.Chrome(**kwargs)
