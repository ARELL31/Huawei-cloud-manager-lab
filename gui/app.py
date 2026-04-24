import sys

import wx

from gui.log import LogRedirector
from gui.panels.config import ConfigDialog
from gui.panels.create import CreatePanel
from gui.panels.delete import DeletePanel
from gui.panels.export import ExportPanel
from gui.panels.list_panel import ListPanel


class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Huawei Cloud IAM Manager",
                         size=(920, 720), style=wx.DEFAULT_FRAME_STYLE)
        self.SetMinSize((780, 580))
        self._build()
        sys.stdout = LogRedirector(self.log)
        self.Centre()
        self.Show()

    def _build(self):
        panel = wx.Panel(self)
        root = wx.BoxSizer(wx.VERTICAL)

        nb = wx.Notebook(panel)
        nb.AddPage(CreatePanel(nb),  "  Crear  ")
        nb.AddPage(DeletePanel(nb),  "  Eliminar  ")
        nb.AddPage(ListPanel(nb),    "  Listar  ")
        nb.AddPage(ExportPanel(nb),  "  Exportar  ")
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
        self._build_menubar()
        self.Bind(wx.EVT_CLOSE, self._on_close)

    def _build_menubar(self):
        menubar = wx.MenuBar()

        menu_file = wx.Menu()
        item_cfg = menu_file.Append(wx.ID_PREFERENCES, "Configuración...\tCtrl+,",
                                    "Editar credenciales y parámetros de conexión")
        menu_file.AppendSeparator()
        menu_file.Append(wx.ID_EXIT, "Salir\tAlt+F4")
        menubar.Append(menu_file, "Archivo")

        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self._on_open_config, item_cfg)
        self.Bind(wx.EVT_MENU, lambda _: self.Close(), id=wx.ID_EXIT)

    def _on_open_config(self, _event):
        dlg = ConfigDialog(self)
        dlg.ShowModal()
        dlg.Destroy()

    def _on_close(self, event):
        if isinstance(sys.stdout, LogRedirector):
            sys.stdout.close()
        sys.stdout = sys.__stdout__
        event.Skip()


def main():
    app = wx.App(False)
    MainFrame()
    app.MainLoop()
