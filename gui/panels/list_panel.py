import wx

from utils.list_resources import (
    list_groups, list_group_users,
    list_ecs_for_group, list_ecs_for_user,
    list_vpcs, list_subnets_for_vpc,
)

from gui.constants import LIST_OPTIONS, LIST_COLUMNS, NEEDS_FILTER
from gui.mixins import ProgressMixin
from gui.widgets import field, run_thread


class ListPanel(ProgressMixin, wx.Panel):
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

        row_filter, self.filter_input = field(self, "Filtro:", "")
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

        root.Add(sres, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=12)

        self._init_progress(root)
        self.SetSizer(root)
        self._on_choice(None)

    def _on_choice(self, event):
        opcion = self.choice.GetStringSelection()
        hint = NEEDS_FILTER.get(opcion)
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
        if opcion in NEEDS_FILTER and not filtro:
            wx.MessageBox(f"Ingresa el {NEEDS_FILTER[opcion].lower()}.", "Aviso",
                          wx.OK | wx.ICON_WARNING, self)
            return

        self.btn_list.Disable()
        self.list_ctrl.ClearAll()
        self.lbl_count.SetLabel("Consultando...")
        self.start_pulse(f"Consultando {opcion.lower()}...")

        def task():
            items = []
            try:
                print(f"\n[CONSULTA] {opcion}" + (f": {filtro}" if filtro else ""))
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
            except Exception as e:
                print(f"[ERROR] Consulta fallida: {e}")
            finally:
                wx.CallAfter(self.stop_progress)
                wx.CallAfter(self._populate, opcion, items)
                wx.CallAfter(self.btn_list.Enable)

        run_thread(task)
