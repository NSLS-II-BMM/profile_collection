from bluesky.callbacks import LivePlot

run_report(__file__)

# LivePlot does not provide very good hooks for doing anything
# beyond very simple data processing. For example, it can't combine
# values from two different fields. Here, we cargo cult most of
# LivePlot.event, but we expect the 'y' value to be a string.

class ExprPlot(LivePlot):
    def event(self, doc):
        "Unpack data from the event and call self.update()."
        # This outer try/except block is needed because multiple event
        # streams will be emitted by the RunEngine and not all event
        # streams will have the keys we want.
        try:
            # This inner try/except block handles seq_num and time, which could
            # be keys in the data or accessing the standard entries in every
            # event.
            try:
                new_x = doc['data'][self.x]
            except KeyError:
                if self.x in ('time', 'seq_num'):
                    new_x = doc[self.x]
                else:
                    raise
            new_y = eval(self.y, doc['data'])
        except KeyError:
            # wrong event stream, skip it
            return

        # Special-case 'time' to plot against against experiment epoch, not
        # UNIX epoch.
        if self.x == 'time' and self._epoch == 'run':
            new_x -= self._epoch_offset

        self.update_caches(new_x, new_y)
        self.update_plot()
