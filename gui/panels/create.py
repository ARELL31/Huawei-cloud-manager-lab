import wx

from utils.iam.create_users import create_users
from utils.iam.enable_users import enable_users
from utils.iam.disable_users import disable_users
from utils.iam.helpers import read_usernames
from utils.csv_validator import get_validation_report

from gui.mixins import ProgressMixin
from gui.widgets import field, confirm, run_thread


class CreatePanel(ProgressMixin, wx.ScrolledWindow):
    _PHASE_LABELS = {
        "iam":    "Creando usuarios IAM",
        "subnet": "Creando subnets",
        "ecs":    "Creando instancias ECS",
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.SetScrollRate(0, 12)
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        box1 = wx.StaticBox(self, label=" Crear Usuarios desde CSV ")
        s1 = wx.StaticBoxSizer(box1, wx.VERTICAL)

        row_csv, self.csv_create = field(self, "Archivo CSV:")
        s1.Add(row_csv, flag=wx.EXPAND | wx.ALL, border=8)

        self.fp_create = wx.FilePickerCtrl(
            self, message="Selecciona el CSV",
            wildcard="CSV (*.csv)|*.csv|Todos los archivos|*.*",
            style=wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST,
        )
        self.fp_create.Bind(wx.EVT_FILEPICKER_CHANGED,
                            lambda e: self.csv_create.SetValue(e.GetPath()))
        s1.Add(self.fp_create, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        row_grp, self.grp_create = field(self, "Grupo:", "Opcional — deja vacío para omitir")
        s1.Add(row_grp, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        self.btn_create = wx.Button(self, label="Crear usuarios")
        self.btn_create.Bind(wx.EVT_BUTTON, self.on_create)
        s1.Add(self.btn_create, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)
        root.Add(s1, flag=wx.EXPAND | wx.ALL, border=12)

        box2 = wx.StaticBox(self, label=" Cambiar Estado de Usuarios ")
        s2 = wx.StaticBoxSizer(box2, wx.VERTICAL)

        row_csv2, self.csv_toggle = field(self, "Archivo CSV:")
        s2.Add(row_csv2, flag=wx.EXPAND | wx.ALL, border=8)

        self.fp_toggle = wx.FilePickerCtrl(
            self, message="Selecciona el CSV",
            wildcard="CSV (*.csv)|*.csv|Todos los archivos|*.*",
            style=wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST,
        )
        self.fp_toggle.Bind(wx.EVT_FILEPICKER_CHANGED,
                            lambda e: self.csv_toggle.SetValue(e.GetPath()))
        s2.Add(self.fp_toggle, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_enable = wx.Button(self, label="Habilitar usuarios")
        self.btn_disable = wx.Button(self, label="Deshabilitar usuarios")
        self.btn_enable.Bind(wx.EVT_BUTTON, self.on_enable)
        self.btn_disable.Bind(wx.EVT_BUTTON, self.on_disable)
        btn_row.Add(self.btn_enable, flag=wx.RIGHT, border=8)
        btn_row.Add(self.btn_disable)
        s2.Add(btn_row, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)
        root.Add(s2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._init_progress(root)
        self.SetSizer(root)

    def _all_buttons(self):
        return (self.btn_create, self.btn_enable, self.btn_disable)

    def _busy(self, state: bool):
        for b in self._all_buttons():
            b.Enable(not state)

    def _get_csv(self, field_ctrl: wx.TextCtrl) -> str | None:
        path = field_ctrl.GetValue().strip()
        if not path:
            wx.MessageBox("Selecciona un archivo CSV primero.", "Aviso",
                          wx.OK | wx.ICON_WARNING, self)
            return None
        return path

    def _validate_and_confirm(self, csv_file: str):
        report = get_validation_report(csv_file)
        if report is None:
            return None
        if not report["users"]:
            wx.MessageBox("El CSV está vacío o no tiene filas de datos.",
                          "Error", wx.OK | wx.ICON_ERROR, self)
            return None
        if report["errors"]:
            msg = "Errores críticos — el CSV no puede procesarse:\n\n"
            msg += "\n".join(f"  • {e}" for e in report["errors"])
            wx.MessageBox(msg, "Errores en el CSV", wx.OK | wx.ICON_ERROR, self)
            return None
        if report["warnings"]:
            msg = "Se encontraron advertencias:\n\n"
            msg += "\n".join(f"  • {w}" for w in report["warnings"])
            msg += "\n\n¿Deseas continuar de todas formas?"
            if not confirm(self, msg):
                return None
        return report

    def on_create(self, event):
        csv_file = self._get_csv(self.csv_create)
        if not csv_file:
            return
        report = self._validate_and_confirm(csv_file)
        if report is None:
            return

        n = len(report["users"])
        group_name = self.grp_create.GetValue().strip() or None
        self._busy(True)

        phases = ["iam", "subnet", "ecs"] if group_name else ["iam"]
        self.start_gauge(n * len(phases), f"Iniciando...  0/{n}")

        _phase_offsets = {p: i * n for i, p in enumerate(phases)}

        def progress(phase, current, total):
            if phase not in _phase_offsets:
                return
            value = _phase_offsets[phase] + current
            label = f"{self._PHASE_LABELS[phase]}  {current}/{total}"
            wx.CallAfter(self.update_gauge, value, label)

        def task():
            print(f"\n[INICIO] Creando usuarios desde '{csv_file}'...")
            create_users(csv_file, group_name=group_name, on_progress=progress)
            wx.CallAfter(self.stop_progress)
            wx.CallAfter(self._busy, False)

        run_thread(task)

    def on_enable(self, event):
        self._toggle_users(enable=True)

    def on_disable(self, event):
        self._toggle_users(enable=False)

    def _toggle_users(self, enable: bool):
        csv_file = self._get_csv(self.csv_toggle)
        if not csv_file:
            return

        try:
            usernames = read_usernames(csv_file)
            n = len(usernames)
        except Exception:
            n = 0

        verb = "Habilitando" if enable else "Deshabilitando"
        action = enable_users if enable else disable_users
        self._busy(True)

        if n > 0:
            self.start_gauge(n, f"{verb} usuarios  0/{n}")
        else:
            self.start_pulse(f"{verb} usuarios...")

        def progress(current, total):
            wx.CallAfter(self.update_gauge, current,
                         f"{verb} usuarios  {current}/{total}")

        def task():
            print(f"\n[INICIO] {verb} usuarios...")
            action(csv_file, on_progress=progress if n > 0 else None)
            wx.CallAfter(self.stop_progress)
            wx.CallAfter(self._busy, False)

        run_thread(task)
