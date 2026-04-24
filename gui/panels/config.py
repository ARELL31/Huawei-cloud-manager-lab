import json
import os

import wx

from gui.constants import HUAWEI_REGIONS
from gui.widgets import field, secret_row


class ConfigPanel(wx.ScrolledWindow):
    _CONFIG_FILE = "config/config.json"

    def __init__(self, parent):
        super().__init__(parent)
        self.SetScrollRate(0, 12)
        self._build()
        self._load()

    def _build(self):
        root = wx.BoxSizer(wx.VERTICAL)

        box1 = wx.StaticBox(self, label=" Credenciales de Acceso ")
        s1 = wx.StaticBoxSizer(box1, wx.VERTICAL)

        row_ak, self.fld_ak = field(self, "Access Key:", "AK — identificador de acceso")
        s1.Add(row_ak, flag=wx.EXPAND | wx.ALL, border=8)

        row_sk, self.fld_sk = secret_row(self, "Secret Key:", "SK — se guarda en config.json")
        s1.Add(row_sk, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        root.Add(s1, flag=wx.EXPAND | wx.ALL, border=12)

        box2 = wx.StaticBox(self, label=" Identificadores de Proyecto ")
        s2 = wx.StaticBoxSizer(box2, wx.VERTICAL)

        row_did, self.fld_domain_id = field(self, "Domain ID:", "ID del dominio raíz")
        s2.Add(row_did, flag=wx.EXPAND | wx.ALL, border=8)

        row_pid, self.fld_project_id = field(self, "Project ID:", "ID del proyecto regional")
        s2.Add(row_pid, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        row_reg = wx.BoxSizer(wx.HORIZONTAL)
        lbl_reg = wx.StaticText(self, label="Región:", size=(90, -1))
        self.fld_region = wx.Choice(self, choices=HUAWEI_REGIONS)
        self.fld_region.SetSelection(0)
        row_reg.Add(lbl_reg, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)
        row_reg.Add(self.fld_region, proportion=1, flag=wx.EXPAND)
        s2.Add(row_reg, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        root.Add(s2, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        box3 = wx.StaticBox(self, label=" Configuración de ECS ")
        s3 = wx.StaticBoxSizer(box3, wx.VERTICAL)

        row_img, self.fld_image_ref = field(self, "Image Ref:", "ID de la imagen base")
        s3.Add(row_img, flag=wx.EXPAND | wx.ALL, border=8)

        row_flv, self.fld_flavor_ref = field(self, "Flavor Ref:", "ej. s6.small.1")
        s3.Add(row_flv, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        row_vt, self.fld_vol_type = field(self, "Tipo de disco:", "SSD, SATA, SAS...")
        s3.Add(row_vt, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        row_vs, self.fld_vol_size = field(self, "Tamaño (GB):", "ej. 40")
        s3.Add(row_vs, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=8)

        root.Add(s3, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.lbl_status = wx.StaticText(self, label="")
        btn_row.Add(self.lbl_status, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)
        btn_save = wx.Button(self, label="Guardar configuración")
        btn_save.Bind(wx.EVT_BUTTON, self._on_save)
        btn_row.Add(btn_save)
        root.Add(btn_row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self.SetSizer(root)

    def _load(self):
        if not os.path.exists(self._CONFIG_FILE):
            self._set_status(
                "config.json no encontrado — completa los campos y guarda.",
                color=(180, 90, 0),
            )
            return
        try:
            with open(self._CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            self.fld_ak.SetValue(cfg.get("ak", ""))
            self.fld_sk.SetValue(cfg.get("sk", ""))
            self.fld_domain_id.SetValue(cfg.get("domain_id", ""))
            self.fld_project_id.SetValue(cfg.get("project_id", ""))
            region = cfg.get("region", "")
            if region in HUAWEI_REGIONS:
                self.fld_region.SetSelection(HUAWEI_REGIONS.index(region))
            ecs = cfg.get("ecs", {})
            self.fld_image_ref.SetValue(ecs.get("image_ref", ""))
            self.fld_flavor_ref.SetValue(ecs.get("flavor_ref", ""))
            self.fld_vol_type.SetValue(ecs.get("root_volume_type", "SSD"))
            self.fld_vol_size.SetValue(str(ecs.get("root_volume_size", 40)))
            self._set_status("Configuración cargada.", color=(0, 130, 0))
        except Exception as e:
            self._set_status(f"Error al cargar: {e}", color=(180, 0, 0))

    def _on_save(self, _event):
        required = [
            ("Access Key",  self.fld_ak),
            ("Secret Key",  self.fld_sk),
            ("Domain ID",   self.fld_domain_id),
            ("Project ID",  self.fld_project_id),
            ("Image Ref",   self.fld_image_ref),
            ("Flavor Ref",  self.fld_flavor_ref),
        ]
        for label, fld in required:
            if not fld.GetValue().strip():
                wx.MessageBox(f"El campo '{label}' es obligatorio.", "Campo vacío",
                              wx.OK | wx.ICON_WARNING, self)
                return

        try:
            vol_size = int(self.fld_vol_size.GetValue().strip())
            if vol_size < 10:
                raise ValueError
        except ValueError:
            wx.MessageBox("El tamaño del disco debe ser un número entero ≥ 10.",
                          "Valor inválido", wx.OK | wx.ICON_WARNING, self)
            return

        cfg = {
            "ak":         self.fld_ak.GetValue().strip(),
            "sk":         self.fld_sk.GetValue().strip(),
            "domain_id":  self.fld_domain_id.GetValue().strip(),
            "project_id": self.fld_project_id.GetValue().strip(),
            "region":     self.fld_region.GetStringSelection(),
            "ecs": {
                "image_ref":        self.fld_image_ref.GetValue().strip(),
                "flavor_ref":       self.fld_flavor_ref.GetValue().strip(),
                "root_volume_type": self.fld_vol_type.GetValue().strip() or "SSD",
                "root_volume_size": vol_size,
            },
        }
        os.makedirs(os.path.dirname(self._CONFIG_FILE), exist_ok=True)
        try:
            with open(self._CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            self._set_status("Configuración guardada correctamente.", color=(0, 130, 0))
        except Exception as e:
            self._set_status(f"Error al guardar: {e}", color=(180, 0, 0))

    def _set_status(self, msg: str, color: tuple):
        self.lbl_status.SetLabel(msg)
        self.lbl_status.SetForegroundColour(wx.Colour(*color))
        self.lbl_status.Refresh()


class ConfigDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="Configuración",
                         size=(580, 640),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(ConfigPanel(self), proportion=1, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.Centre()
