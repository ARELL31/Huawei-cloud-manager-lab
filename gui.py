import sys
import threading
import wx

from utils.iam.create_users import create_users
from utils.iam.enable_users import enable_users
from utils.iam.disable_users import disable_users
from utils.delete_all import (
    delete_all, delete_single_user, delete_single_ecs,
    delete_single_subnet, delete_single_vpc,
)
from utils.list_resources import (
    list_groups, list_group_users,
    list_ecs_for_group, list_ecs_for_user,
    list_vpcs, list_subnets_for_vpc,
)
from utils.csv_validator import get_validation_report

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

    def __init__(self, target: wx.TextCtrl):
        self._target = target

    def write(self, text: str):
        wx.CallAfter(self._append, text)

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

def _field(parent, label, hint=""):
    row = wx.BoxSizer(wx.HORIZONTAL)
    lbl = wx.StaticText(parent, label=label, size=(90, -1))
    lbl.SetFont(lbl.GetFont())
    ctrl = wx.TextCtrl(parent, size=(340, -1))
    if hint:
        ctrl.SetHint(hint)
    row.Add(lbl, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)
    row.Add(ctrl, proportion=1, flag=wx.EXPAND)
    return row, ctrl


def _confirm(parent, msg: str) -> bool:
    dlg = wx.MessageDialog(parent, msg, "Confirmar",
                           wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
    result = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    return result


def _run(func):
    t = threading.Thread(target=func, daemon=True)
    t.start()

class CreatePanel(wx.ScrolledWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetScrollRate(0, 12)
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        box1 = wx.StaticBox(self, label=" Crear Usuarios desde CSV ")
        s1 = wx.StaticBoxSizer(box1, wx.VERTICAL)

        row_csv, self.csv_create = _field(self, "Archivo CSV:")
        s1.Add(row_csv, flag=wx.EXPAND | wx.ALL, border=8)

        self.fp_create = wx.FilePickerCtrl(
            self, message="Selecciona el CSV",
            wildcard="CSV (*.csv)|*.csv|Todos los archivos|*.*",
            style=wx.FLP_USE_TEXTCTRL | wx.FLP_OPEN | wx.FLP_FILE_MUST_EXIST,
        )
        self.fp_create.Bind(wx.EVT_FILEPICKER_CHANGED,
                            lambda e: self.csv_create.SetValue(e.GetPath()))
        s1.Add(self.fp_create, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        row_grp, self.grp_create = _field(self, "Grupo:", "Opcional — deja vacío para omitir")
        s1.Add(row_grp, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        self.btn_create = wx.Button(self, label="Crear usuarios")
        self.btn_create.Bind(wx.EVT_BUTTON, self.on_create)
        s1.Add(self.btn_create, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)
        root.Add(s1, flag=wx.EXPAND | wx.ALL, border=12)

        box2 = wx.StaticBox(self, label=" Cambiar Estado de Usuarios ")
        s2 = wx.StaticBoxSizer(box2, wx.VERTICAL)

        row_csv2, self.csv_toggle = _field(self, "Archivo CSV:")
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

        self.SetSizer(root)

    def _all_buttons(self):
        return (self.btn_create, self.btn_enable, self.btn_disable)

    def _busy(self, state: bool):
        for b in self._all_buttons():
            b.Enable(not state)

    def _get_csv(self, field: wx.TextCtrl) -> str | None:
        path = field.GetValue().strip()
        if not path:
            wx.MessageBox("Selecciona un archivo CSV primero.", "Aviso",
                          wx.OK | wx.ICON_WARNING, self)
            return None
        return path

    def _validate_and_confirm(self, csv_file: str) -> bool:
        report = get_validation_report(csv_file)
        if report is None:
            return False
        if not report["users"]:
            wx.MessageBox("El CSV está vacío o no tiene filas de datos.",
                          "Error", wx.OK | wx.ICON_ERROR, self)
            return False
        if report["errors"]:
            msg = "Errores críticos — el CSV no puede procesarse:\n\n"
            msg += "\n".join(f"  • {e}" for e in report["errors"])
            wx.MessageBox(msg, "Errores en el CSV", wx.OK | wx.ICON_ERROR, self)
            return False
        if report["warnings"]:
            msg = "Se encontraron advertencias:\n\n"
            msg += "\n".join(f"  • {w}" for w in report["warnings"])
            msg += "\n\n¿Deseas continuar de todas formas?"
            if not _confirm(self, msg):
                return False
        return True

    def on_create(self, event):
        csv_file = self._get_csv(self.csv_create)
        if not csv_file:
            return
        if not self._validate_and_confirm(csv_file):
            return
        group_name = self.grp_create.GetValue().strip() or None
        self._busy(True)

        def task():
            print(f"\n[INICIO] Creando usuarios desde '{csv_file}'...")
            create_users(csv_file, group_name=group_name)
            wx.CallAfter(self._busy, False)

        _run(task)

    def on_enable(self, event):
        csv_file = self._get_csv(self.csv_toggle)
        if not csv_file:
            return
        self._busy(True)

        def task():
            print(f"\n[INICIO] Habilitando usuarios...")
            enable_users(csv_file)
            wx.CallAfter(self._busy, False)

        _run(task)

    def on_disable(self, event):
        csv_file = self._get_csv(self.csv_toggle)
        if not csv_file:
            return
        self._busy(True)

        def task():
            print(f"\n[INICIO] Deshabilitando usuarios...")
            disable_users(csv_file)
            wx.CallAfter(self._busy, False)

        _run(task)

RESOURCE_TYPES = ["Usuario", "ECS", "Subnet", "VPC"]

class DeletePanel(wx.ScrolledWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetScrollRate(0, 12)
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        box1 = wx.StaticBox(self, label=" Eliminar Grupo y Todos sus Recursos ")
        s1 = wx.StaticBoxSizer(box1, wx.VERTICAL)

        row_g, self.grp_del = _field(self, "Grupo:", "Nombre del grupo")
        s1.Add(row_g, flag=wx.EXPAND | wx.ALL, border=8)

        self.btn_del_group = wx.Button(self, label="Eliminar grupo completo")
        self.btn_del_group.SetForegroundColour(wx.Colour(160, 0, 0))
        self.btn_del_group.Bind(wx.EVT_BUTTON, self.on_del_group)
        s1.Add(self.btn_del_group, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)
        root.Add(s1, flag=wx.EXPAND | wx.ALL, border=12)

        box2 = wx.StaticBox(self, label=" Eliminar Recurso Individual ")
        s2 = wx.StaticBoxSizer(box2, wx.VERTICAL)

        row_type = wx.BoxSizer(wx.HORIZONTAL)
        row_type.Add(wx.StaticText(self, label="Tipo:", size=(90, -1)),
                     flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)
        self.res_type = wx.Choice(self, choices=RESOURCE_TYPES)
        self.res_type.SetSelection(0)
        self.res_type.Bind(wx.EVT_CHOICE, self._on_type_change)
        row_type.Add(self.res_type)
        s2.Add(row_type, flag=wx.ALL, border=8)

        row_name, self.res_name = _field(self, "Nombre:", "Nombre del recurso")
        s2.Add(row_name, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        row_extra, self.res_extra = _field(self, "Grupo / VPC:", "Grupo (usuario) o VPC (subnet)")
        s2.Add(row_extra, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)
        self._row_extra_sizer = row_extra
        self._row_extra_widgets = row_extra.GetChildren()

        self.btn_del_ind = wx.Button(self, label="Eliminar recurso")
        self.btn_del_ind.SetForegroundColour(wx.Colour(160, 0, 0))
        self.btn_del_ind.Bind(wx.EVT_BUTTON, self.on_del_individual)
        s2.Add(self.btn_del_ind, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)
        root.Add(s2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._extra_label = row_extra.GetItem(0).GetWindow()
        self._extra_field = self.res_extra
        self.SetSizer(root)
        self._on_type_change(None)

    def _on_type_change(self, event):
        tipo = self.res_type.GetStringSelection()
        show = tipo in ("Usuario", "Subnet")
        self._extra_label.Show(show)
        self._extra_field.Show(show)
        if tipo == "Usuario":
            self._extra_label.SetLabel("Grupo:")
            self._extra_field.SetHint("Nombre del grupo (opcional)")
        elif tipo == "Subnet":
            self._extra_label.SetLabel("VPC:")
            self._extra_field.SetHint("Nombre de la VPC")
        self.Layout()

    def _busy(self, state: bool):
        self.btn_del_group.Enable(not state)
        self.btn_del_ind.Enable(not state)

    def on_del_group(self, event):
        name = self.grp_del.GetValue().strip()
        if not name:
            wx.MessageBox("Ingresa el nombre del grupo.", "Aviso",
                          wx.OK | wx.ICON_WARNING, self)
            return
        msg = (f"Se eliminarán TODOS los recursos del grupo '{name}':\n\n"
               "  • Instancias ECS\n  • Subnets\n  • VPC\n  • Usuarios IAM\n\n"
               "Esta acción no se puede deshacer. ¿Confirmas?")
        if not _confirm(self, msg):
            return
        self._busy(True)

        def task():
            print(f"\n[INICIO] Eliminando grupo '{name}' y sus recursos...")
            delete_all(name)
            wx.CallAfter(self._busy, False)

        _run(task)

    def on_del_individual(self, event):
        tipo = self.res_type.GetStringSelection()
        name = self.res_name.GetValue().strip()
        extra = self.res_extra.GetValue().strip()

        if not name:
            wx.MessageBox("Ingresa el nombre del recurso.", "Aviso",
                          wx.OK | wx.ICON_WARNING, self)
            return
        if tipo == "Subnet" and not extra:
            wx.MessageBox("Ingresa el nombre de la VPC para la subnet.", "Aviso",
                          wx.OK | wx.ICON_WARNING, self)
            return
        if not _confirm(self, f"¿Eliminar {tipo} '{name}'? Esta acción no se puede deshacer."):
            return
        self._busy(True)

        def task():
            print(f"\n[INICIO] Eliminando {tipo} '{name}'...")
            if tipo == "Usuario":
                delete_single_user(name, extra)
            elif tipo == "ECS":
                delete_single_ecs(name)
            elif tipo == "Subnet":
                delete_single_subnet(name, extra)
            elif tipo == "VPC":
                delete_single_vpc(name)
            wx.CallAfter(self._busy, False)

        _run(task)

LIST_OPTIONS = [
    "Grupos IAM",
    "Usuarios de un grupo",
    "ECS de un grupo",
    "ECS de un usuario",
    "VPCs",
    "Subnets de una VPC",
]

LIST_COLUMNS = {
    "Grupos IAM":           [("Nombre", 200), ("ID", 300), ("Descripcion", 220)],
    "Usuarios de un grupo": [("Nombre", 200), ("ID", 300), ("Estado", 120)],
    "ECS de un grupo":      [("Nombre", 200), ("Propietario", 150), ("ID", 280), ("Estado", 110)],
    "ECS de un usuario":    [("Nombre", 200), ("ID", 300), ("Estado", 120)],
    "VPCs":                 [("Nombre", 200), ("ID", 300), ("CIDR", 140), ("Estado", 110)],
    "Subnets de una VPC":   [("Nombre", 200), ("ID", 300), ("CIDR", 140), ("Estado", 110)],
}

_NEEDS_FILTER = {
    "Usuarios de un grupo": "Nombre del grupo",
    "ECS de un grupo":      "Nombre del grupo",
    "ECS de un usuario":    "Nombre del usuario",
    "Subnets de una VPC":   "Nombre de la VPC",
}


class ListPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        box = wx.StaticBox(self, label=" Consulta ")
        sctrl = wx.StaticBoxSizer(box, wx.VERTICAL)

        row_opt = wx.BoxSizer(wx.HORIZONTAL)
        row_opt.Add(wx.StaticText(self, label="Listar:", size=(90, -1)),
                    flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)
        self.choice = wx.Choice(self, choices=LIST_OPTIONS)
        self.choice.SetSelection(0)
        self.choice.Bind(wx.EVT_CHOICE, self._on_choice)
        row_opt.Add(self.choice)
        sctrl.Add(row_opt, flag=wx.ALL, border=8)

        row_filter, self.filter_input = _field(self, "Filtro:", "")
        sctrl.Add(row_filter, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)
        self._filter_label = row_filter.GetItem(0).GetWindow()

        self.btn_list = wx.Button(self, label="Consultar")
        self.btn_list.Bind(wx.EVT_BUTTON, self.on_list)
        sctrl.Add(self.btn_list, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)
        root.Add(sctrl, flag=wx.EXPAND | wx.ALL, border=12)

        res_box = wx.StaticBox(self, label=" Resultados ")
        sres = wx.StaticBoxSizer(res_box, wx.VERTICAL)

        self.list_ctrl = wx.ListCtrl(
            self, style=wx.LC_REPORT | wx.BORDER_SIMPLE | wx.LC_HRULES | wx.LC_VRULES
        )
        sres.Add(self.list_ctrl, proportion=1, flag=wx.EXPAND | wx.ALL, border=6)

        self.lbl_count = wx.StaticText(self, label="")
        sres.Add(self.lbl_count, flag=wx.LEFT | wx.BOTTOM, border=6)

        root.Add(sres, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self.SetSizer(root)
        self._on_choice(None)

    def _on_choice(self, event):
        opcion = self.choice.GetStringSelection()
        hint = _NEEDS_FILTER.get(opcion)
        show = hint is not None
        self._filter_label.Show(show)
        self.filter_input.Show(show)
        if show:
            self._filter_label.SetLabel(hint.split(" de ")[0].capitalize() + ":")
            self.filter_input.SetHint(hint)
        self.Layout()

    def _setup_columns(self, opcion: str):
        self.list_ctrl.ClearAll()
        for i, (name, width) in enumerate(LIST_COLUMNS.get(opcion, [])):
            self.list_ctrl.InsertColumn(i, name, width=width)

    def _populate(self, opcion: str, items: list):
        self._setup_columns(opcion)
        for item in items:
            row = self._to_row(opcion, item)
            idx = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), row[0])
            for col, val in enumerate(row[1:], start=1):
                self.list_ctrl.SetItem(idx, col, str(val))
        n = len(items)
        self.lbl_count.SetLabel(f"{n} resultado{'s' if n != 1 else ''}" if n else "Sin resultados.")

    @staticmethod
    def _to_row(opcion: str, item) -> list:
        if opcion == "Grupos IAM":
            return [item.name, item.id, item.description or "—"]
        if opcion == "Usuarios de un grupo":
            return [item.name, item.id, "Habilitado" if item.enabled else "Deshabilitado"]
        if opcion == "ECS de un grupo":
            return [item.name, (item.metadata or {}).get("owner", "—"), item.id, item.status]
        if opcion == "ECS de un usuario":
            return [item.name, item.id, item.status]
        if opcion in ("VPCs", "Subnets de una VPC"):
            return [item.name, item.id, item.cidr, item.status]
        return []

    def on_list(self, event):
        opcion = self.choice.GetStringSelection()
        filtro = self.filter_input.GetValue().strip()
        if opcion in _NEEDS_FILTER and not filtro:
            wx.MessageBox(f"Ingresa el {_NEEDS_FILTER[opcion].lower()}.", "Aviso",
                          wx.OK | wx.ICON_WARNING, self)
            return

        self.btn_list.Disable()
        self.list_ctrl.ClearAll()
        self.lbl_count.SetLabel("Consultando...")

        def task():
            print(f"\n[CONSULTA] {opcion}" + (f": {filtro}" if filtro else ""))
            items = []
            if opcion == "Grupos IAM":
                items = list_groups()
            elif opcion == "Usuarios de un grupo":
                items = list_group_users(filtro)
            elif opcion == "ECS de un grupo":
                items = list_ecs_for_group(filtro)
            elif opcion == "ECS de un usuario":
                items = list_ecs_for_user(filtro)
            elif opcion == "VPCs":
                items = list_vpcs()
            elif opcion == "Subnets de una VPC":
                items = list_subnets_for_vpc(filtro)
            wx.CallAfter(self._populate, opcion, items)
            wx.CallAfter(self.btn_list.Enable)

        _run(task)

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Huawei Cloud IAM Manager",
                         size=(920, 720), style=wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize((780, 580))
        self._build()
        self._redirect()
        self.Centre()
        self.Show()

    def _build(self):
        panel = wx.Panel(self)
        root = wx.BoxSizer(wx.VERTICAL)

        nb = wx.Notebook(panel)
        nb.AddPage(CreatePanel(nb), "  Crear  ")
        nb.AddPage(DeletePanel(nb), "  Eliminar  ")
        nb.AddPage(ListPanel(nb), "  Listar  ")
        root.Add(nb, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)

        log_box = wx.StaticBox(panel, label=" Registro de operaciones ")
        slog = wx.StaticBoxSizer(log_box, wx.VERTICAL)
        self.log = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.HSCROLL,
            size=(-1, 150),
        )
        self.log.SetFont(wx.Font(
            9, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL
        ))
        slog.Add(self.log, proportion=1, flag=wx.EXPAND | wx.ALL, border=4)

        btn_clear = wx.Button(panel, label="Limpiar")
        btn_clear.Bind(wx.EVT_BUTTON, lambda _: self.log.Clear())
        slog.Add(btn_clear, flag=wx.ALIGN_RIGHT | wx.ALL, border=4)

        root.Add(slog, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        panel.SetSizer(root)
        self.CreateStatusBar().SetStatusText("Listo")

        self.Bind(wx.EVT_CLOSE, self._on_close)

    def _redirect(self):
        sys.stdout = LogRedirector(self.log)

    def _on_close(self, event):
        sys.stdout = sys.__stdout__
        event.Skip()

def main():
    app = wx.App(False)
    MainFrame()
    app.MainLoop()


if __name__ == "__main__":
    main()
