import wx

from utils.delete_all import (
    delete_all, delete_single_user, delete_single_ecs,
    delete_single_subnet, delete_single_vpc,
)

from gui.constants import RESOURCE_TYPES
from gui.mixins import ProgressMixin
from gui.widgets import field, confirm, run_thread


class DeletePanel(ProgressMixin, wx.ScrolledWindow):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetScrollRate(0, 12)
        self._build()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        box1 = wx.StaticBox(self, label=" Eliminar Grupo y Todos sus Recursos ")
        s1 = wx.StaticBoxSizer(box1, wx.VERTICAL)

        row_g, self.grp_del = field(self, "Grupo:", "Nombre del grupo")
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

        row_name, self.res_name = field(self, "Nombre:", "Nombre del recurso")
        s2.Add(row_name, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        row_extra, self.res_extra = field(self, "Grupo / VPC:", "")
        s2.Add(row_extra, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)
        self._extra_label = row_extra.GetItem(0).GetWindow()
        self._extra_field = self.res_extra

        self.btn_del_ind = wx.Button(self, label="Eliminar recurso")
        self.btn_del_ind.SetForegroundColour(wx.Colour(160, 0, 0))
        self.btn_del_ind.Bind(wx.EVT_BUTTON, self.on_del_individual)
        s2.Add(self.btn_del_ind, flag=wx.ALIGN_RIGHT | wx.ALL, border=8)
        root.Add(s2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._init_progress(root)
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
        if not confirm(self, msg):
            return
        self._busy(True)
        self.start_pulse(f"Eliminando grupo '{name}'...")

        def task():
            try:
                print(f"\n[INICIO] Eliminando grupo '{name}' y sus recursos...")
                delete_all(name)
            except Exception as e:
                print(f"[ERROR] Operación interrumpida: {e}")
            finally:
                wx.CallAfter(self.stop_progress)
                wx.CallAfter(self._busy, False)

        run_thread(task)

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
        if not confirm(self, f"¿Eliminar {tipo} '{name}'? Esta acción no se puede deshacer."):
            return
        self._busy(True)
        self.start_pulse(f"Eliminando {tipo} '{name}'...")

        def task():
            try:
                print(f"\n[INICIO] Eliminando {tipo} '{name}'...")
                if tipo == "Usuario":
                    delete_single_user(name, extra)
                elif tipo == "ECS":
                    delete_single_ecs(name)
                elif tipo == "Subnet":
                    delete_single_subnet(name, extra)
                elif tipo == "VPC":
                    delete_single_vpc(name)
            except Exception as e:
                print(f"[ERROR] Operación interrumpida: {e}")
            finally:
                wx.CallAfter(self.stop_progress)
                wx.CallAfter(self._busy, False)

        run_thread(task)
