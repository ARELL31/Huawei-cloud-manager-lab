import threading

import wx


class SecretCtrl(wx.Panel):
    def __init__(self, parent, hint: str = ""):
        super().__init__(parent)
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._masked = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self._plain = wx.TextCtrl(self)
        if hint:
            self._masked.SetHint(hint)
            self._plain.SetHint(hint)
        self._plain.Hide()

        self._btn = wx.Button(self, label="Mostrar", size=(70, -1))
        self._btn.Bind(wx.EVT_BUTTON, self._on_toggle)

        sizer.Add(self._masked, proportion=1, flag=wx.EXPAND | wx.RIGHT, border=4)
        sizer.Add(self._plain,  proportion=1, flag=wx.EXPAND | wx.RIGHT, border=4)
        sizer.Add(self._btn, flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(sizer)

    def _on_toggle(self, event):
        if self._plain.IsShown():
            self._masked.SetValue(self._plain.GetValue())
            self._plain.Hide()
            self._masked.Show()
            self._btn.SetLabel("Mostrar")
        else:
            self._plain.SetValue(self._masked.GetValue())
            self._masked.Hide()
            self._plain.Show()
            self._btn.SetLabel("Ocultar")
        self.Layout()
        self.GetParent().Layout()

    def GetValue(self) -> str:
        return self._plain.GetValue() if self._plain.IsShown() else self._masked.GetValue()

    def SetValue(self, value: str):
        self._masked.SetValue(value)
        self._plain.SetValue(value)


def field(parent, label: str, hint: str = ""):
    row = wx.BoxSizer(wx.HORIZONTAL)
    lbl = wx.StaticText(parent, label=label, size=(90, -1))
    ctrl = wx.TextCtrl(parent, size=(340, -1))
    if hint:
        ctrl.SetHint(hint)
    row.Add(lbl, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)
    row.Add(ctrl, proportion=1, flag=wx.EXPAND)
    return row, ctrl


def secret_row(parent, label: str, hint: str = ""):
    row = wx.BoxSizer(wx.HORIZONTAL)
    lbl = wx.StaticText(parent, label=label, size=(90, -1))
    ctrl = SecretCtrl(parent, hint=hint)
    row.Add(lbl, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=6)
    row.Add(ctrl, proportion=1, flag=wx.EXPAND)
    return row, ctrl


def confirm(parent, msg: str) -> bool:
    dlg = wx.MessageDialog(parent, msg, "Confirmar",
                           wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING)
    result = dlg.ShowModal() == wx.ID_YES
    dlg.Destroy()
    return result


def run_thread(func):
    threading.Thread(target=func, daemon=True).start()
