import wx

from utils.ecs.manage_ecs import (
    get_servers_for_group, get_servers_for_user,
    batch_start, batch_stop, batch_reboot,
    list_resize_flavors, resize_server,
)
from gui.mixins import ProgressMixin
from gui.widgets import field, confirm, run_thread


# ── Diálogo de selección de flavor ────────────────────────────────────────────

class ResizeDialog(wx.Dialog):
    def __init__(self, parent, server, flavors: list):
        super().__init__(
            parent,
            title=f"Cambiar flavor — {server.name}",
            size=(660, 460),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self._flavor_ref: str | None = None
        self._build(server, flavors)
        self.Centre()

    def _build(self, server, flavors):
        sizer = wx.BoxSizer(wx.VERTICAL)

        current = getattr(server.flavor, "name", "—") if server.flavor else "—"
        info = wx.StaticText(
            self,
            label=f"Instancia: {server.name}    Estado: {server.status}    Flavor actual: {current}",
        )
        sizer.Add(info, flag=wx.ALL, border=12)

        self.list_ctrl = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.BORDER_SIMPLE | wx.LC_SINGLE_SEL
                  | wx.LC_HRULES | wx.LC_VRULES,
        )
        for i, (col, w) in enumerate([
            ("Nombre", 190), ("vCPU", 65), ("RAM (GB)", 90), ("ID", 280),
        ]):
            self.list_ctrl.InsertColumn(i, col, width=w)

        for flavor in sorted(flavors, key=lambda f: (int(f.vcpus or 0), int(f.ram or 0))):
            ram_gb = round(int(flavor.ram or 0) / 1024, 1)
            idx = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), flavor.name or "")
            self.list_ctrl.SetItem(idx, 1, str(flavor.vcpus or ""))
            self.list_ctrl.SetItem(idx, 2, str(ram_gb))
            self.list_ctrl.SetItem(idx, 3, flavor.id or "")

        sizer.Add(self.list_ctrl, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=12)

        hint = wx.StaticText(self, label="Selecciona el nuevo flavor y haz clic en Aplicar.")
        hint.SetForegroundColour(wx.Colour(90, 90, 90))
        sizer.Add(hint, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=10)

        btn_sizer = wx.StdDialogButtonSizer()
        self.btn_ok = wx.Button(self, wx.ID_OK, "Aplicar")
        self.btn_ok.Disable()
        btn_sizer.AddButton(self.btn_ok)
        btn_sizer.AddButton(wx.Button(self, wx.ID_CANCEL, "Cancelar"))
        btn_sizer.Realize()
        sizer.Add(btn_sizer, flag=wx.EXPAND | wx.ALL, border=12)

        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED,   self._on_flavor_select)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, lambda _: self.btn_ok.Disable())
        self.SetSizer(sizer)

    def _on_flavor_select(self, event):
        self._flavor_ref = self.list_ctrl.GetItem(event.GetIndex(), 3).GetText()
        self.btn_ok.Enable(bool(self._flavor_ref))

    def get_flavor_ref(self) -> str | None:
        return self._flavor_ref


# ── Panel principal ────────────────────────────────────────────────────────────

class EcsManagePanel(ProgressMixin, wx.ScrolledWindow):
    _TARGET_TYPES = ["Grupo", "Usuario"]

    def __init__(self, parent):
        super().__init__(parent)
        self.SetScrollRate(0, 12)
        self._servers: list = []
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        # ── Búsqueda ──────────────────────────────────────────────────────────
        box_s = wx.StaticBox(self, label=" Buscar ECS ")
        s_s = wx.StaticBoxSizer(box_s, wx.VERTICAL)

        row_type = wx.BoxSizer(wx.HORIZONTAL)
        row_type.Add(wx.StaticText(self, label="Tipo:", size=(90, -1)),
                     flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)
        self.target_type = wx.Choice(self, choices=self._TARGET_TYPES)
        self.target_type.SetSelection(0)
        row_type.Add(self.target_type)
        s_s.Add(row_type, flag=wx.ALL, border=8)

        row_name, self.fld_name = field(self, "Nombre:", "Nombre del grupo o usuario")
        s_s.Add(row_name, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        self.btn_search = wx.Button(self, label="Buscar ECS")
        self.btn_search.Bind(wx.EVT_BUTTON, self.on_search)
        s_s.Add(self.btn_search, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)

        root.Add(s_s, flag=wx.EXPAND | wx.ALL, border=12)

        # ── Resultados ────────────────────────────────────────────────────────
        box_r = wx.StaticBox(self, label=" Instancias encontradas ")
        s_r = wx.StaticBoxSizer(box_r, wx.VERTICAL)

        self.list_ctrl = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.BORDER_SIMPLE | wx.LC_SINGLE_SEL
                  | wx.LC_HRULES | wx.LC_VRULES,
            size=(-1, 160),
        )
        for i, (col, w) in enumerate([
            ("Nombre", 200), ("Propietario", 150), ("ID", 280), ("Estado", 110),
        ]):
            self.list_ctrl.InsertColumn(i, col, width=w)

        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED,   self._on_row_select)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._on_row_deselect)

        s_r.Add(self.list_ctrl, flag=wx.EXPAND | wx.ALL, border=6)

        self.lbl_count = wx.StaticText(self, label="Sin resultados.")
        s_r.Add(self.lbl_count, flag=wx.LEFT | wx.BOTTOM, border=6)

        root.Add(s_r, proportion=1, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        # ── Iniciar / Detener / Reiniciar ─────────────────────────────────────
        box_a = wx.StaticBox(self, label=" Acción sobre todas las instancias encontradas ")
        s_a = wx.StaticBoxSizer(box_a, wx.VERTICAL)

        self.chk_force = wx.CheckBox(
            self, label="Forzar (HARD) — corte inmediato sin esperar al SO"
        )
        s_a.Add(self.chk_force, flag=wx.ALL, border=8)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_start  = wx.Button(self, label="▶  Iniciar")
        self.btn_stop   = wx.Button(self, label="■  Detener")
        self.btn_reboot = wx.Button(self, label="↺  Reiniciar")

        self.btn_start.SetForegroundColour(wx.Colour(0, 130, 0))
        self.btn_stop.SetForegroundColour(wx.Colour(160, 0, 0))
        self.btn_reboot.SetForegroundColour(wx.Colour(0, 80, 160))

        self.btn_start.Bind(wx.EVT_BUTTON,  lambda e: self.on_action("start"))
        self.btn_stop.Bind(wx.EVT_BUTTON,   lambda e: self.on_action("stop"))
        self.btn_reboot.Bind(wx.EVT_BUTTON, lambda e: self.on_action("reboot"))

        for btn in self._action_buttons():
            btn.Disable()
            btn_row.Add(btn, flag=wx.RIGHT, border=8)

        s_a.Add(btn_row, flag=wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)
        root.Add(s_a, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        # ── Upgrade / Downgrade ───────────────────────────────────────────────
        box_u = wx.StaticBox(self, label=" Upgrade / Downgrade ")
        s_u = wx.StaticBoxSizer(box_u, wx.VERTICAL)

        hint = wx.StaticText(
            self,
            label="Selecciona una instancia en la tabla para cambiar su flavor (vCPUs y RAM).",
        )
        hint.SetForegroundColour(wx.Colour(90, 90, 90))
        s_u.Add(hint, flag=wx.ALL, border=8)

        self.btn_resize = wx.Button(self, label="↕  Cambiar Flavor…")
        self.btn_resize.Disable()
        self.btn_resize.Bind(wx.EVT_BUTTON, self.on_resize)
        s_u.Add(self.btn_resize, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)

        root.Add(s_u, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._init_progress(root)
        self.SetSizer(root)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _action_buttons(self):
        return (self.btn_start, self.btn_stop, self.btn_reboot)

    def _set_busy(self, busy: bool):
        self.btn_search.Enable(not busy)
        has_results = bool(self._servers)
        for btn in self._action_buttons():
            btn.Enable(not busy and has_results)
        self._update_resize_btn()

    def _update_resize_btn(self):
        not_busy = self.btn_search.IsEnabled()
        has_selection = self.list_ctrl.GetFirstSelected() != -1
        self.btn_resize.Enable(not_busy and has_selection)

    def _on_row_select(self, _event):
        self._update_resize_btn()

    def _on_row_deselect(self, _event):
        self._update_resize_btn()

    def _selected_server(self):
        idx = self.list_ctrl.GetFirstSelected()
        if idx == -1 or idx >= len(self._servers):
            return None
        return self._servers[idx]

    # ── búsqueda ──────────────────────────────────────────────────────────────

    def on_search(self, event):
        name = self.fld_name.GetValue().strip()
        if not name:
            wx.MessageBox("Ingresa el nombre del grupo o usuario.", "Aviso",
                          wx.OK | wx.ICON_WARNING, self)
            return

        tipo = self.target_type.GetStringSelection()
        self._servers = []
        self.list_ctrl.DeleteAllItems()
        self.lbl_count.SetLabel("Buscando…")
        for btn in self._action_buttons():
            btn.Disable()
        self.btn_resize.Disable()
        self._set_busy(True)
        self.start_pulse(f"Buscando ECS de {tipo.lower()} '{name}'…")

        def task():
            try:
                servers = (
                    get_servers_for_group(name)
                    if tipo == "Grupo"
                    else get_servers_for_user(name)
                )
            except Exception as e:
                print(f"[ERROR] {e}")
                servers = []
            finally:
                wx.CallAfter(self.stop_progress)
                wx.CallAfter(self._on_search_done, servers)

        run_thread(task)

    def _on_search_done(self, servers: list):
        self._servers = servers
        self.list_ctrl.DeleteAllItems()
        for s in servers:
            owner = (s.metadata or {}).get("owner", "—")
            idx = self.list_ctrl.InsertItem(self.list_ctrl.GetItemCount(), s.name)
            self.list_ctrl.SetItem(idx, 1, owner)
            self.list_ctrl.SetItem(idx, 2, s.id)
            self.list_ctrl.SetItem(idx, 3, s.status)
        n = len(servers)
        self.lbl_count.SetLabel(
            f"{n} instancia{'s' if n != 1 else ''} encontrada{'s' if n != 1 else ''}."
            if n else "Sin resultados."
        )
        self._set_busy(False)

    # ── iniciar / detener / reiniciar ─────────────────────────────────────────

    def on_action(self, action: str):
        if not self._servers:
            return

        n = len(self._servers)
        force = self.chk_force.GetValue()
        labels = {"start": "iniciar", "stop": "detener", "reboot": "reiniciar"}
        verb = labels[action].capitalize()

        mode_note = f" (HARD — forzado)" if action in ("stop", "reboot") and force else ""
        msg = (
            f"¿{verb}{mode_note} {n} instancia{'s' if n != 1 else ''}?\n\n"
            + "\n".join(f"  • {s.name}  [{s.status}]" for s in self._servers)
            + "\n\nLa operación se envía al cloud y se ejecuta de forma asíncrona."
        )
        if not confirm(self, msg):
            return

        servers = list(self._servers)
        self._set_busy(True)
        self.start_pulse(f"{verb}ando {n} ECS…")

        def task():
            try:
                if action == "start":
                    batch_start(servers)
                elif action == "stop":
                    batch_stop(servers, force=force)
                elif action == "reboot":
                    batch_reboot(servers, force=force)
            except Exception as e:
                print(f"[ERROR] Operación interrumpida: {e}")
            finally:
                wx.CallAfter(self.stop_progress)
                wx.CallAfter(self._set_busy, False)

        run_thread(task)

    # ── upgrade / downgrade ───────────────────────────────────────────────────

    def on_resize(self, _event):
        server = self._selected_server()
        if not server:
            return

        self._set_busy(True)
        self.start_pulse(f"Cargando flavors disponibles para '{server.name}'…")

        def fetch():
            try:
                flavors = list_resize_flavors(server.id)
            except Exception as e:
                print(f"[ERROR] {e}")
                flavors = []
            finally:
                wx.CallAfter(self.stop_progress)
                wx.CallAfter(self._set_busy, False)
                if flavors:
                    wx.CallAfter(self._open_resize_dialog, server, flavors)
                else:
                    wx.CallAfter(
                        wx.MessageBox,
                        "No se encontraron flavors disponibles para esta instancia.",
                        "Sin opciones", wx.OK | wx.ICON_INFORMATION,
                    )

        run_thread(fetch)

    def _open_resize_dialog(self, server, flavors: list):
        dlg = ResizeDialog(self, server, flavors)
        if dlg.ShowModal() != wx.ID_OK:
            dlg.Destroy()
            return
        flavor_ref = dlg.get_flavor_ref()
        dlg.Destroy()

        if not flavor_ref:
            return

        self._set_busy(True)
        self.start_pulse(f"Cambiando flavor de '{server.name}'…")

        def task():
            try:
                resize_server(server.id, flavor_ref)
            except Exception as e:
                print(f"[ERROR] Operación interrumpida: {e}")
            finally:
                wx.CallAfter(self.stop_progress)
                wx.CallAfter(self._set_busy, False)

        run_thread(task)
