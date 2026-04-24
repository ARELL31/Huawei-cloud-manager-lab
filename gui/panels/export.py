import os
from datetime import datetime

import wx

from utils.export_snapshot import collect_snapshot, write_csv, write_json
from gui.mixins import ProgressMixin
from gui.widgets import run_thread


class ExportPanel(ProgressMixin, wx.ScrolledWindow):
    _FORMATS = ["CSV", "JSON"]
    _EXPORTS_DIR = "exports"

    def __init__(self, parent):
        super().__init__(parent)
        self.SetScrollRate(0, 12)
        self._build()
        self._refresh_default_path()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox(self, label=" Exportar Snapshot de Recursos ")
        s = wx.StaticBoxSizer(box, wx.VERTICAL)

        # — Formato ——————————————————————————————————————————
        row_fmt = wx.BoxSizer(wx.HORIZONTAL)
        row_fmt.Add(wx.StaticText(self, label="Formato:", size=(90, -1)),
                    flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)
        self.fmt_choice = wx.Choice(self, choices=self._FORMATS)
        self.fmt_choice.SetSelection(0)
        self.fmt_choice.Bind(wx.EVT_CHOICE, self._on_fmt_change)
        row_fmt.Add(self.fmt_choice)
        s.Add(row_fmt, flag=wx.ALL, border=8)

        # — Archivo de salida ————————————————————————————————
        row_path = wx.BoxSizer(wx.HORIZONTAL)
        row_path.Add(wx.StaticText(self, label="Archivo:", size=(90, -1)),
                     flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)
        self.fld_path = wx.TextCtrl(self)
        row_path.Add(self.fld_path, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=4)
        btn_browse = wx.Button(self, label="…", size=(32, -1))
        btn_browse.Bind(wx.EVT_BUTTON, self._on_browse)
        row_path.Add(btn_browse, flag=wx.ALIGN_CENTER_VERTICAL)
        s.Add(row_path, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        # — Qué incluir ——————————————————————————————————————
        info = wx.StaticText(
            self,
            label="Incluye: todos los grupos IAM · usuarios (nombre, ID, estado) · ECS (nombre, ID, estado, IPs)",
        )
        info.SetForegroundColour(wx.Colour(90, 90, 90))
        s.Add(info, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        # — Botón ————————————————————————————————————————————
        self.btn_export = wx.Button(self, label="Exportar snapshot")
        self.btn_export.Bind(wx.EVT_BUTTON, self.on_export)
        s.Add(self.btn_export, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)

        root.Add(s, flag=wx.EXPAND | wx.ALL, border=12)
        self._init_progress(root)
        self.SetSizer(root)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _ext(self) -> str:
        return self.fmt_choice.GetStringSelection().lower()

    def _refresh_default_path(self):
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        self.fld_path.SetValue(
            os.path.join(self._EXPORTS_DIR, f"snapshot_{ts}.{self._ext()}")
        )

    def _on_fmt_change(self, event):
        current = self.fld_path.GetValue()
        for ext in ("csv", "json"):
            if current.endswith(f".{ext}"):
                self.fld_path.SetValue(current[: -len(ext)] + self._ext())
                return
        self._refresh_default_path()

    def _on_browse(self, event):
        fmt = self.fmt_choice.GetStringSelection()
        wildcard = (
            "CSV (*.csv)|*.csv|Todos los archivos|*.*"
            if fmt == "CSV"
            else "JSON (*.json)|*.json|Todos los archivos|*.*"
        )
        dlg = wx.FileDialog(
            self, "Guardar snapshot como",
            defaultFile=os.path.basename(self.fld_path.GetValue()),
            wildcard=wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.fld_path.SetValue(dlg.GetPath())
        dlg.Destroy()

    # ── export ───────────────────────────────────────────────────────────────

    def on_export(self, event):
        path = self.fld_path.GetValue().strip()
        if not path:
            wx.MessageBox("Especifica un archivo de salida.", "Aviso",
                          wx.OK | wx.ICON_WARNING, self)
            return

        fmt = self.fmt_choice.GetStringSelection()
        self.btn_export.Disable()
        self.start_pulse("Consultando cloud…")

        def task():
            try:
                print(f"\n[INICIO] Generando snapshot ({fmt})…")
                snapshot = collect_snapshot()

                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                writer = write_csv if fmt == "CSV" else write_json
                n_groups, n_users, n_ecs = writer(snapshot, path)

                print(
                    f"[OK] Snapshot exportado — "
                    f"{n_groups} grupo(s), {n_users} usuario(s), {n_ecs} ECS"
                )
                print(f"[OK] Archivo: {os.path.abspath(path)}")
            except Exception as e:
                print(f"[ERROR] No se pudo exportar: {e}")
            finally:
                wx.CallAfter(self.stop_progress)
                wx.CallAfter(self.btn_export.Enable)

        run_thread(task)
