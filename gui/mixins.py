import wx


class ProgressMixin:
    def _init_progress(self, parent_sizer: wx.BoxSizer):
        row = wx.BoxSizer(wx.HORIZONTAL)

        self._lbl_step = wx.StaticText(self, label="", size=(260, -1))
        self._gauge = wx.Gauge(self, style=wx.GA_HORIZONTAL | wx.GA_SMOOTH)

        row.Add(self._lbl_step, flag=wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, border=8)
        row.Add(self._gauge, proportion=1, flag=wx.ALIGN_CENTER_VERTICAL)

        parent_sizer.Add(row, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, border=12)

        self._pulse_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda _: self._gauge.Pulse(), self._pulse_timer)

        self._hide_progress()

    def start_pulse(self, label: str = ""):
        self._gauge.SetRange(100)
        self._lbl_step.SetLabel(label)
        self._show_progress()
        self._pulse_timer.Start(80)

    def start_gauge(self, total: int, label: str = ""):
        self._pulse_timer.Stop()
        self._gauge.SetRange(total)
        self._gauge.SetValue(0)
        self._lbl_step.SetLabel(label)
        self._show_progress()

    def update_gauge(self, value: int, label: str = ""):
        self._gauge.SetValue(value)
        if label:
            self._lbl_step.SetLabel(label)

    def stop_progress(self):
        self._pulse_timer.Stop()
        self._gauge.SetValue(0)
        self._hide_progress()

    def _show_progress(self):
        self._lbl_step.Show()
        self._gauge.Show()
        self.Layout()

    def _hide_progress(self):
        self._lbl_step.Hide()
        self._gauge.Hide()
        self.Layout()
