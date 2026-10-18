"""Check / edit / install the weekly launchd job without touching raw plist or launchctl.

    python src/ops/launchd_ctl.py status                 # lịch, trạng thái, lần chạy cuối, log mới nhất
    python src/ops/launchd_ctl.py schedule mon 09:00     # đổi lịch (sửa plist trong repo + nạp lại)
    python src/ops/launchd_ctl.py install                # copy plist repo -> ~/Library/LaunchAgents + nạp
    python src/ops/launchd_ctl.py run                    # chạy ngay (kickstart)
    python src/ops/launchd_ctl.py uninstall              # gỡ job

Source of truth is the plist in this folder (committed); `install`/`schedule` copy it to
~/Library/LaunchAgents and reload. Stdlib only.
"""

import argparse
import os
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

LABEL = "com.dataspi.batdongsan-weekly"
REPO_PLIST = Path(__file__).with_name(f"{LABEL}.plist")
INSTALLED_PLIST = Path.home() / "Library/LaunchAgents" / f"{LABEL}.plist"
DOMAIN = f"gui/{os.getuid()}"
DAYS = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}
DAY_NAMES = {v: k for k, v in DAYS.items()}


def sh(*cmd, check=True):
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def load_plist(path: Path) -> dict:
    with path.open("rb") as f:
        return plistlib.load(f)


def reload():
    """Copy repo plist to LaunchAgents and (re)load it."""
    sh("plutil", "-lint", str(REPO_PLIST))
    INSTALLED_PLIST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_PLIST, INSTALLED_PLIST)
    sh("launchctl", "bootout", f"{DOMAIN}/{LABEL}", check=False)  # not loaded yet -> ignore
    sh("launchctl", "bootstrap", DOMAIN, str(INSTALLED_PLIST))


def cmd_status(_):
    if not INSTALLED_PLIST.exists():
        print(f"CHƯA cài: {INSTALLED_PLIST} không tồn tại. Chạy `install`.")
        return
    p = load_plist(INSTALLED_PLIST)
    sci = p.get("StartCalendarInterval", {})
    drift = "" if INSTALLED_PLIST.read_bytes() == REPO_PLIST.read_bytes() else "  (KHÁC bản trong repo!)"
    print(f"File     : {INSTALLED_PLIST}{drift}")
    print(f"Lịch     : {DAY_NAMES.get(sci.get('Weekday'), '?')} {sci.get('Hour', 0):02d}:{sci.get('Minute', 0):02d}")
    print(f"Script   : {' '.join(p['ProgramArguments'])}")
    print(f"RunAtLoad: {p.get('RunAtLoad', False)}")

    r = sh("launchctl", "print", f"{DOMAIN}/{LABEL}", check=False)
    if r.returncode:
        print("Trạng thái: KHÔNG được nạp vào launchd (chạy `install`)")
    else:
        info = {}
        for line in r.stdout.splitlines():
            k, _, v = line.strip().partition(" = ")
            info.setdefault(k, v)
        print(f"Trạng thái: {info.get('state')} | số lần chạy: {info.get('runs')}"
              f" | last exit: {info.get('last exit code')}")

    logs = Path(p["StandardOutPath"]).parent
    latest = sorted(logs.glob("pipeline_*.log"))
    if latest:
        print(f"Log mới nhất: {latest[-1]}")
        print("  ...\n  " + "\n  ".join(latest[-1].read_text(errors="replace").splitlines()[-5:]))
    else:
        print("Chưa có log pipeline_*.log nào (job chưa từng chạy).")
    err = Path(p["StandardErrorPath"])
    if err.exists() and err.stat().st_size:
        print(f"Cảnh báo: {err} có nội dung (launchd không khởi động được script?)")


def cmd_schedule(a):
    day = DAYS.get(a.day.lower()[:3])
    if day is None:
        sys.exit(f"Thứ không hợp lệ: {a.day} (mon..sun)")
    hour, minute = (int(x) for x in a.time.split(":"))
    # plistlib drops the explanatory XML comment at the top of the template; patch values in place instead.
    text = REPO_PLIST.read_text()
    new = text
    for key, val in (("Weekday", day), ("Hour", hour), ("Minute", minute)):
        new = re.sub(rf"(<key>{key}</key>\s*<integer>)\d+(</integer>)", rf"\g<1>{val}\g<2>", new, count=1)
    REPO_PLIST.write_text(new)
    reload()
    print(f"Đã đặt lịch: {a.day} {hour:02d}:{minute:02d} và nạp lại launchd. (Nhớ commit plist trong repo.)")


def cmd_install(_):
    reload()
    print("Đã cài và nạp job.")


def cmd_run(_):
    sh("launchctl", "kickstart", f"{DOMAIN}/{LABEL}")
    print("Đã kích hoạt chạy ngay. Xem tiến độ: tail -f logs/pipeline_*.log (file mới nhất)")


def cmd_uninstall(_):
    sh("launchctl", "bootout", f"{DOMAIN}/{LABEL}", check=False)
    INSTALLED_PLIST.unlink(missing_ok=True)
    print("Đã gỡ job.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    s = sub.add_parser("schedule")
    s.add_argument("day", help="mon|tue|wed|thu|fri|sat|sun")
    s.add_argument("time", help="HH:MM (24h)")
    s.set_defaults(fn=cmd_schedule)
    sub.add_parser("install").set_defaults(fn=cmd_install)
    sub.add_parser("run").set_defaults(fn=cmd_run)
    sub.add_parser("uninstall").set_defaults(fn=cmd_uninstall)
    a = ap.parse_args()
    try:
        a.fn(a)
    except subprocess.CalledProcessError as e:
        sys.exit(f"Lỗi: {' '.join(e.cmd)}\n{e.stderr}")


if __name__ == "__main__":
    main()
