import os
from datetime import datetime

import wx


class LogRedirector:
    _COLORS = {
        "[OK]":       (0,   130, 0),
        "[ERROR]":    (180, 0,   0),
        "[AVISO]":    (180, 90,  0),
        "[WARN]":     (180, 90,  0),
        "[INFO]":     (0,   80,  160),
        "[INICIO]":   (100, 0,   140),
        "[CONSULTA]": (0,   80,  160),
    }
    _LOG_DIR = "logs"

    def __init__(self, target: wx.TextCtrl):
        self._target = target
        self._buf = ""
        self._file = self._open_log_file()
        self._write_log(f"{'=' * 54}")
        self._write_log(f"Sesión iniciada — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._write_log(f"{'=' * 54}")

    def _open_log_file(self):
        os.makedirs(self._LOG_DIR, exist_ok=True)
        path = os.path.join(self._LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        return open(path, "a", encoding="utf-8")

    def _write_log(self, line: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self._file.write(f"[{ts}] {line}\n")
        self._file.flush()

    def write(self, text: str):
        wx.CallAfter(self._append, text)
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if line.strip():
                self._write_log(line)

    def _append(self, text: str):
        color = wx.BLACK
        for tag, rgb in self._COLORS.items():
            if tag in text:
                color = wx.Colour(*rgb)
                break
        self._target.SetDefaultStyle(wx.TextAttr(color))
        self._target.AppendText(text)
        self._target.SetDefaultStyle(wx.TextAttr(wx.BLACK))

    def flush(self):
        pass

    def close(self):
        if self._buf.strip():
            self._write_log(self._buf)
        self._write_log(f"Sesión cerrada — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._file.close()
