import configparser
import glob
import os
import re
import shutil
from pathlib import Path

import matplotlib
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy
import psutil
from bluesky.plan_stubs import mv, mvr, null, sleep
from BMM import user_ns as user_ns_module
from BMM.derivedplot import close_all_plots, close_last_plot
from BMM.functions import (
    bold_msg,
    countdown,
    disconnected_msg,
    error_msg,
    go_msg,
    info_msg,
    isfloat,
    list_msg,
    now,
    present_options,
    url_msg,
    verbosebold_msg,
    warning_msg,
    whisper,
)
from BMM.kafka import kafka_message
from BMM.linescans import linescan
from BMM.logging import img_to_slack, post_to_slack, report
from BMM.macrobuilder import BMMMacroBuilder
from BMM.periodictable import PERIODIC_TABLE, edge_energy

# from BMM.purpose        import purpose
from BMM.suspenders import BMM_clear_suspenders, BMM_clear_to_start, BMM_suspenders
from BMM.xafs_functions import conventional_grid
from lmfit.models import StepModel
from openpyxl import load_workbook
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO, Signal
from PIL import Image
from scipy.ndimage import center_of_mass

user_ns = vars(user_ns_module)

from BMM.user_ns.motors import xafs_garot, xafs_pitch, xafs_x, xafs_y


class GlancingAngle(Device):
    """A class capturing the movement and control of the glancing angle
    spinner stage.

    Attributes
    ==========
    spinner1 .. spinner8 : EpicsSignal
        The EpicsSignal component for spinner #1 .. 8
    spin : Bool
        When True, the ga.to() method will start the spinner
    home : float
        Position in xafs_garot of spinner 0
    inverted : str
        A string used to recognize whether the linear scan steps up or down
    flat : list
        The linear and pitch positions of the flat sample on the current spinner
    y_uid : str
        The DataBroker UID of the most recent linear against It scan
    pitch_uid : str
        The DataBroker UID of the most recent xafs_pitch against It scan
    f_uid : str
        The DataBroker UID of the most recent linear against fluorescence scan
    alignment_filename : str
        The fully resolved path to the three-panel, auto-alignment png image


    Methods
    =======
    current : return the current spoinner number as an integer
    reset : return xafs_garot to its home position
    on : turn on the specified spinner
    off : turn off the specified spinner
    alloff : turn off all spinners
    alloff_plan : turn off all spinners as a plan
    to : move to the specified spinner, turn off all other spinners, turn on this spinner
    auto_align : perform an automated alignment for the current spinner

    Notes
    =====

    The auto_align plan does some ugly shit to plot the results of
    each individual step in the alignment procedure.  It uses
    matplotlib to fashion the plot, but switches to a headless backend
    before plotting.  It then saves the plot to throw-away png file.
    PIL is then used to funnel the display of the plot out to
    xdg-open.

    On xf06bm-ws3, the desktop is configured to have ImageMagick's
    display be the default view for a png file.  Thus, PIL is forking
    a process and running display to show the plot to the user.

    Care is taken to clean up after PIL (which leaves png files in
    /tmp/) and to close any running display processes (that is, a
    process running ImageMagick's display).

    The reason this is needed is that the user needs visual feedback
    to know whether the alignment procedure is proceeding
    successfully.

    This plotting solution presents images of the alignment steps
    which are non-interactive -- the user cannot query the plot to
    obtain a motor position, for example.

    However, it has the great advantage of not running afoul of the
    fact that ipython and Qt are running on different threads.  Thus
    the full plot will be shown to the user and interacting with the
    plot window (for example, resizing it) will not crash bsui.

    See the clean_img() method to details of the clean up process.

    Sigh....

    """

    spinner1 = Cpt(EpicsSignal, "OutPt08:Data-Sel")
    spinner2 = Cpt(EpicsSignal, "OutPt09:Data-Sel")
    spinner3 = Cpt(EpicsSignal, "OutPt10:Data-Sel")
    spinner4 = Cpt(EpicsSignal, "OutPt11:Data-Sel")
    spinner5 = Cpt(EpicsSignal, "OutPt12:Data-Sel")
    spinner6 = Cpt(EpicsSignal, "OutPt13:Data-Sel")
    spinner7 = Cpt(EpicsSignal, "OutPt14:Data-Sel")
    spinner8 = Cpt(EpicsSignal, "OutPt15:Data-Sel")
    # rotation

    spin = True
    automatic = True
    home = 0
    garot = xafs_garot
    inverted = ""
    flat = [0, 0]
    y_uid = ""
    pitch_uid = ""
    f_uid = ""
    alignment_filename = ""
    _orientation = "parallel"
    toss = os.path.join(user_ns["BMMuser"].folder, "snapshots", "toss.png")
    img = None  # Image.open(os.path.join(user_ns['BMMuser'].folder, 'snapshots', 'toss.png'))

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        if value.lower() == "perpendicular":
            self._orientation = "perpendicular"
            user_ns["gawheel"].orientation = "perpendicular"
        else:
            self._orientation = "parallel"
            user_ns["gawheel"].orientation = "parallel"

    def current(self):
        """Return the current spinner number as an integer"""
        pos = self.garot.position
        cur = pos % 360
        here = (9 - round(cur / 45)) % 8
        if here == 0:
            here = 8
        return here

    def reset(self):
        """Return glancing angle stage to spinner 1"""
        yield from self.alloff_plan()
        yield from mv(self.garot, self.home)
        report("Returned to spinner 1 at %d degrees and turned off all spinners" % self.home, level="bold")

    def valid(self, number=None):
        """Check that an argument is an integer between 1 and 8"""
        if number is None:
            return False
        if type(number) is not int:
            return False
        if number < 1 or number > 8:
            return False
        return True

    def on(self, number):
        """Turn on the specified spinner"""
        if self.spin is False:
            print(warning_msg('The spinners are currently disabled.  do "ga.spin = True" to re-enable.'))
            return
        if not self.valid(number):
            print(error_msg("The fans are numbered from 1 to 8"))
            return
        this = getattr(self, f"spinner{number}")
        this.put(1)

    def off(self, number=None):
        """Turn off the specified spinner"""
        if number is None:
            self.alloff()
            return
        if not self.valid(number):
            print(error_msg("The fans are numbered from 1 to 8"))
            return
        this = getattr(self, f"spinner{number}")
        this.put(0)

    def alloff(self):
        """Turn off all spinners"""
        for i in range(1, 9):
            self.off(i)

    def alloff_plan(self):
        """Turn off all spinners as a plan"""
        save = user_ns["RE"].msg_hook
        user_ns["RE"].msg_hook = None
        for i in range(1, 9):
            this = getattr(self, f"spinner{i}")
            yield from mv(this, 0)
        user_ns["RE"].msg_hook = save

    def to(self, number):
        """Rotate to the specified spinner. Turn off all other spinners.  Turn
        on the specified spinner."""
        if not self.valid(number):
            print(error_msg("The fans are numbered from 1 to 8"))
            yield from null()
            return
        yield from self.alloff_plan()
        distance = number - self.current()
        if distance > 4:
            distance = distance - 8
        elif distance < -4:
            distance = 8 + distance
        angle = -45 * distance
        yield from mvr(self.garot, angle)
        if self.spin is True:
            this = getattr(self, f"spinner{number}")
            yield from mv(this, 1)

    def clean_img(self):
        """Kill any outstanding "display" processes (i.e. ImageMagick's
        display).  Then remove any .PNG files PIL has left lying
        around in /tmp.  Finally, explicitly close the previous
        filehandle.

        This takes no care to verify neither that PIL launched the
        display process nor that PIL wrote the .PNG file in /tmp.

        Note that this will kill any other "display" processes
        running.  At NSLS-II, the centrally managed screen locker is
        configured to use feh to show a transparent png when the
        screen is locked.  Thus, display was chosen as the viewer
        rather than feh (although ownership would likely preclude
        terminating the screenlocker process).

        """
        for proc in psutil.process_iter():
            if proc.name() == "display":
                proc.kill()
        for f in glob.glob("/tmp/tmp*.PNG"):
            try:
                os.remove(f)
            except:
                print(whisper(f"unable to delete {f} while cleaning up /tmp"))
            if self.img is not None:
                self.img.close()

    def align_pitch(self, force=False):
        """Find the peak of xafs_pitch scan against It. Plot the
        result. Move to the peak."""
        xafs_pitch = user_ns["xafs_pitch"]
        uid = yield from linescan(xafs_pitch, "it", -2.5, 2.5, 51, pluck=False, force=force)
        close_last_plot()
        table = user_ns["db"][-1].table()
        pitch = table["xafs_pitch"]
        signal = table["It"] / table["I0"]
        target = signal.idxmax()
        yield from mv(xafs_pitch, pitch[target])
        kafka_message(
            {
                "glancing_angle": "pitch",
                "motor": "xafs_pitch",
                "center": pitch[target],
                "amplitude": signal.max(),
                "spinner": self.current(),
                "xaxis": list(pitch),
                "data": list(signal),
                "uid": uid,
            }
        )
        # self.pitch_plot(pitch, signal)

    def align_linear(self, force=False, drop=None):
        """Fit an error function to the linear scan against It. Plot the
        result. Move to the centroid of the error function."""
        if self.orientation == "parallel":
            motor = user_ns["xafs_liny"]
        else:
            motor = user_ns["xafs_linx"]
        uid = yield from linescan(motor, "it", -2.3, 2.3, 51, pluck=False)
        close_last_plot()
        table = user_ns["db"][-1].table()
        yy = table[motor.name]
        signal = table["It"] / table["I0"]
        if drop is not None:
            yy = yy[:-drop]
            signal = signal[:-drop]
        if float(signal[2]) > list(signal)[-2]:
            ss = -(signal - signal[2])
            self.inverted = "inverted "
        else:
            ss = signal - signal[2]
            self.inverted = ""
        mod = StepModel(form="erf")
        pars = mod.guess(ss, x=numpy.array(yy))
        out = mod.fit(ss, pars, x=numpy.array(yy))
        print(whisper(out.fit_report(min_correl=0)))
        target = out.params["center"].value
        yield from mv(motor, target)
        kafka_message(
            {
                "glancing_angle": "linear",
                "motor": motor.name,
                "center": target,
                "amplitude": out.params["amplitude"].value,
                "inverted": self.inverted,
                "spinner": self.current(),
                "xaxis": list(yy),
                "data": list(ss),
                "best_fit": list(out.best_fit),
                "uid": uid,
            }
        )

        # self.y_plot(yy, out)

    def align_fluo(self, force=False):
        BMMuser = user_ns["BMMuser"]
        if self.orientation == "parallel":
            motor = user_ns["xafs_liny"]
        else:
            motor = user_ns["xafs_linx"]
        uid = yield from linescan(motor, "xs", -2.3, 2.3, 51, pluck=False, force=force)
        self.f_uid = user_ns["db"].v2[-1].metadata["start"]["uid"]
        tf = user_ns["db"][-1].table()
        yy = tf[motor.name]
        signal = (tf[BMMuser.xs1] + tf[BMMuser.xs2] + tf[BMMuser.xs3] + tf[BMMuser.xs4]) / tf["I0"]
        # if BMMuser.element in ('Cr', 'Zr'):
        centroid = yy[signal.idxmax()]
        # else:
        #    com = int(center_of_mass(signal)[0])+1
        #    centroid = yy[com]
        yield from mv(motor, centroid)
        kafka_message(
            {
                "glancing_angle": "fluo",
                "motor": motor.name,
                "center": centroid,
                "amplitude": signal.max(),
                "inverted": self.inverted,
                "spinner": self.current(),
                "xaxis": list(yy),
                "data": list(signal),
                "uid": uid,
            }
        )

    def auto_align(self, pitch=2, drop=None):
        """Align a sample on a spinner automatically.  This performs 5 scans.
        The first four iterate twice between linear and pitch
        against the signal in It.  This find the flat position.

        Then the sample is pitched to the requested angle and a fifth
        scan is done to optimize the linear motor position against the
        fluorescence signal.

        The linear scans against It look like a step-down function.
        The center of this step is found as the centroid of a fitted
        error function.

        The xafs_pitch scan should be peaked.  Move to the max of the
        signal.

        The linear scan against fluorescence ideally looks like a
        flat-topped peak.  Move to the center of mass.

        At the end, a three-panel figure is drawn showing the last
        three scans.  This is posted to Slack.  It also finds its way
        into the dossier as a record of the quality of the alignment.

        Arguments
        =========
        pitch : int
          The angle at which to make the glancing angle measurements.
        drop : int or None
          If not None, then this many points will be dropped from the
          end of linear scan against transmission when fitting the error
          function. This is an attempt to deal gracefully with leakage
          through the adhesive at very high energy.

        """
        BMMuser = user_ns["BMMuser"]
        if BMMuser.macro_dryrun:
            report(f"Auto-aligning glancing angle stage, spinner {self.current()}", level="bold", slack=False)
            print(
                info_msg(
                    f"\nBMMuser.macro_dryrun is True.  Sleeping for %.1f seconds at spinner %d.\n"
                    % (BMMuser.macro_sleep, self.current())
                )
            )
            countdown(BMMuser.macro_sleep)
            return (yield from null())

        report(f"Auto-aligning glancing angle stage, spinner {self.current()}", level="bold", slack=True)

        BMM_suspenders()
        kafka_message(
            {
                "glancing_angle": "start",
                "filename": os.path.join(BMMuser.folder, "snapshots", f"spinner{self.current()}-alignment-{now()}.png"),
            }
        )

        ## first pass in transmission
        yield from self.align_linear(drop=drop)
        yield from self.align_pitch()

        ## for realsies X or Y in transmission
        yield from self.align_linear(drop=drop)
        self.y_uid = user_ns["db"].v2[-1].metadata["start"]["uid"]

        ## for realsies Y in pitch
        yield from self.align_pitch()
        self.pitch_uid = user_ns["db"].v2[-1].metadata["start"]["uid"]

        ## record the flat position
        if self.orientation == "parallel":
            motor = user_ns["xafs_y"]
        else:
            motor = user_ns["xafs_x"]
        self.flat = [motor.position, user_ns["xafs_pitch"].position]

        ## move to measurement angle and align
        yield from mvr(user_ns["xafs_pitch"], pitch)
        yield from self.align_fluo()
        kafka_message({"glancing_angle": "stop"})

        ## make a pretty picture, post it to slack
        # self.alignment_plot(self.y_uid, self.pitch_uid, self.f_uid)
        # try:
        #     img_to_slack(self.alignment_filename)
        # except:
        #     post_to_slack(f'failed to post image: {self.alignment_filename}')
        #     pass
        BMM_clear_suspenders()

    def flatten(self):
        """Return the stage to its nominally flat position."""
        xafs_pitch = user_ns["xafs_pitch"]
        if self.orientation == "parallel":
            motor = user_ns["xafs_y"]
        else:
            motor = user_ns["xafs_x"]
        if self.flat != [0, 0]:
            yield from mv(motor, self.flat[0], xafs_pitch, self.flat[1])

    def dossier_entry(self):
        thistext = '	    <div id="boxinst">\n'
        thistext += "	      <h3>Instrument: Glancing angle stage</h3>\n"
        thistext += "	      <ul>\n"
        thistext += f"               <li><b>Spinner:</b> {self.current()}</li>\n"
        if self.automatic is True:
            thistext += "               <li><b>Alignment:</b> automatic</li>\n"
            thistext += f"               <li><b>Tilt angle:</b> {xafs_pitch.position - self.flat[1]:.1f}</li>\n"
        else:
            thistext += "               <li><b>Alignment:</b> manual</li>\n"
            thistext += f"               <li><b>Tilt angle:</b> {xafs_pitch.position:.1f}</li>\n"
        thistext += f'               <li><b>Spinning:</b> {"yes" if self.spin else "no"}</li>\n'
        thistext += "	      </ul>\n"
        thistext += "	    </div>\n"
        return thistext

    def pitch_plot(self, pitch, signal, filename=None):
        thisagg = matplotlib.get_backend()
        matplotlib.use("Agg")  # produce a plot without screen display
        target = signal.idxmax()
        close_all_plots()
        # plt.cla()
        plt.plot(pitch, signal)
        plt.scatter(pitch[target], signal.max(), s=160, marker="x", color="green")
        plt.xlabel("xafs_pitch (deg)")
        plt.ylabel("It/I0")
        plt.title(f"pitch scan, spinner {self.current()}")
        plt.plot()
        self.toss = os.path.join(user_ns["BMMuser"].folder, "snapshots", "toss.png")
        plt.savefig(self.toss)
        matplotlib.use(thisagg)  # return to screen display
        self.clean_img()
        self.img = Image.open(self.toss)
        self.img.show()
        # plt.draw()
        # plt.show()
        # plt.figure().canvas.draw_idle()
        # plt.pause(0.05)

    def y_plot(self, yy, out, filename=None):
        # plt.cla()
        thisagg = matplotlib.get_backend()
        matplotlib.use("Agg")  # produce a plot without screen display
        close_all_plots()
        plt.scatter(yy, out.data)
        plt.plot(yy, out.best_fit, color="red")
        plt.scatter(out.params["center"].value, out.params["amplitude"].value / 2, s=160, marker="x", color="green")
        if self.orientation == "parallel":
            plt.xlabel("xafs_y (mm)")
            direction = "Y"
        else:
            plt.xlabel("xafs_x (mm)")
            direction = "X"
        plt.ylabel(f"{self.inverted}data and error function")
        plt.title(f"fit to {direction} scan, spinner {self.current()}")
        plt.plot()
        self.toss = os.path.join(user_ns["BMMuser"].folder, "snapshots", "toss.png")
        plt.savefig(self.toss)
        matplotlib.use(thisagg)  # return to screen display
        self.clean_img()
        self.img = Image.open(self.toss)
        self.img.show()
        # plt.draw()
        # plt.show()
        # plt.figure().canvas.draw_idle()
        # plt.pause(0.05)

    def alignment_plot(self, yt, pitch, yf):
        """Make a pretty, three-panel plot at the end of an auto-alignment"""
        BMMuser = user_ns["BMMuser"]
        thisagg = matplotlib.get_backend()
        matplotlib.use("Agg")  # produce a plot without screen display
        close_all_plots()
        fig = plt.figure(tight_layout=True)  # , figsize=(9,6))
        gs = gridspec.GridSpec(1, 3)

        if self.orientation == "parallel":
            motor = "xafs_y"
        else:
            motor = "xafs_x"

        t = fig.add_subplot(gs[0, 0])
        tt = user_ns["db"][yt].table()
        yy = tt[motor]
        signal = tt["It"] / tt["I0"]
        if float(signal[2]) > list(signal)[-2]:
            ss = -(signal - signal[2])
            self.inverted = "inverted "
        else:
            ss = signal - signal[2]
            self.inverted = ""
        mod = StepModel(form="erf")
        pars = mod.guess(ss, x=numpy.array(yy))
        out = mod.fit(ss, pars, x=numpy.array(yy))
        t.scatter(yy, out.data)
        t.plot(yy, out.best_fit, color="red")
        t.scatter(out.params["center"].value, out.params["amplitude"].value / 2, s=120, marker="x", color="green")
        t.set_xlabel(f"{motor} (mm)")
        t.set_ylabel(f"{self.inverted}data and error function")

        p = fig.add_subplot(gs[0, 1])
        tp = user_ns["db"][pitch].table()
        xp = tp["xafs_pitch"]
        signal = tp["It"] / tp["I0"]
        target = signal.idxmax()
        p.plot(xp, signal)
        p.scatter(xp[target], signal.max(), s=120, marker="x", color="green")
        p.set_xlabel("xafs_pitch (deg)")
        p.set_ylabel("It/I0")
        p.set_title(f"alignment of spinner {self.current()}")

        f = fig.add_subplot(gs[0, 2])
        tf = user_ns["db"][yf].table()
        yy = tf[motor]
        signal = (tf[BMMuser.xs1] + tf[BMMuser.xs2] + tf[BMMuser.xs3] + tf[BMMuser.xs4]) / tf["I0"]
        # if BMMuser.element in ('Zr', 'Sc', 'Nb'):
        com = signal.idxmax()
        centroid = yy[com]
        # else:
        # com = int(center_of_mass(signal)[0])+1
        # centroid = yy[com]
        f.plot(yy, signal)
        f.scatter(centroid, signal[com], s=120, marker="x", color="green")
        f.set_xlabel(f"{motor} (mm)")
        f.set_ylabel("If/I0")

        fig.canvas.draw()
        fig.canvas.flush_events()
        self.alignment_filename = os.path.join(
            BMMuser.folder, "snapshots", f"spinner{self.current()}-alignment-{now()}.png"
        )
        plt.savefig(self.alignment_filename)
        matplotlib.use(thisagg)  # return to screen display
        shutil.copyfile(self.alignment_filename, self.toss)
        self.clean_img()
        self.img = Image.open(os.path.join(user_ns["BMMuser"].folder, "snapshots", "toss.png"))
        self.img.show()
        # plt.show()
        # fig.canvas.draw_idle()
        # plt.pause(0.05)


class GlancingAngleMacroBuilder(BMMMacroBuilder):
    """A class for parsing specially constructed spreadsheets and
    generating macros for measuring XAS on the BMM glancing angle
    stage.

    Examples
    --------
    >>> mb = GlancingAngleMacroBuilder()
    >>> mb.spreadsheet('wheel1.xlsx')
    >>> mb.write_macro()

    """

    def _write_macro(self):
        """Write a macro paragraph for each sample described in the
        spreadsheet.  A paragraph consists of line to move to the
        correct spinner, lines to find or move to the center-aligned
        location in pitch and Y, lines to move to and from the correct
        glancing angle value, a line to change the edge energy (if
        needed), a line to measure the XAFS using the correct set of
        control parameters, and a line to close plot windows after the
        scan.
        """
        element, edge, focus = (None, None, None)

        if self.nreps > 1:
            self.content = self.tab + f"for reps in range({self.nreps}):\n\n"
            self.tab = " " * 12

        for m in self.measurements:

            if m["default"] is True:
                element = m["element"]
                edge = m["edge"]
                continue
            if self.skip_row(m) is True:
                continue

            #######################################
            # default element/edge(/focus) values #
            #######################################
            for k in ("element", "edge", "method", "focus", "spin", "angle"):
                if m[k] is None:
                    m[k] = self.measurements[0][k]

            ##########################
            # change edge, if needed #
            ##########################
            focus = False
            if m["focus"] == "focused":
                focus = True
            if self.do_first_change is True:
                self.content += self.tab + "yield from change_edge('%s', edge='%s', focus=%r)\n" % (
                    m["element"],
                    m["edge"],
                    focus,
                )
                self.do_first_change = False
                self.totaltime += 4

            elif m["element"] != element or m["edge"] != edge:  # focus...
                element = m["element"]
                edge = m["edge"]
                self.content += self.tab + "yield from change_edge('%s', edge='%s', focus=%r)\n" % (
                    m["element"],
                    m["edge"],
                    focus,
                )
                self.totaltime += 4

            else:
                if self.verbose:
                    self.content += self.tab + "## staying at %s %s\n" % (m["element"], m["edge"])
                pass

            #######################
            # move to next sample #
            #######################
            self.content += self.tab + f'ga.spin = {m["spin"]}\n'

            ###############################
            # move to correct slit height #
            ###############################
            if m["slitheight"] is not None:
                if self.check_limit(user_ns["slits3"].vsize, m["slitheight"]) is False:
                    return False
                self.content += self.tab + f'yield from mv(slits3.vsize, {m["slitheight"]})\n'

            #####################################
            # move to correct detector position #
            #####################################
            if m["detectorx"] is not None:
                if self.check_limit(user_ns["xafs_det"], m["detectorx"]) is False:
                    return False
                self.content += self.tab + "yield from mv(xafs_det, %.2f)\n" % m["detectorx"]
            self.content += self.tab + "yield from mvr(xafs_det, 5)\n"
            self.content += self.tab + f'yield from ga.to({m["slot"]})\n'

            if self.orientation == "parallel":
                motor = "xafs_y"
            else:
                motor = "xafs_x"

            #############################################################
            # lower stage and measure reference channel for calibration #
            #############################################################
            fname = self.make_filename(m)
            self.content += self.tab + "if ref is True:\n"
            self.content += self.tab + self.tab + f"yield from mvr({motor}, -5)\n"
            self.content += (
                self.tab
                + self.tab
                + f'yield from xafs("{self.basename}.ini", mode="reference", filename="{m["element"]}foil_{fname}", nscans=1, sample="{m["element"]} foil", element="{m["element"]}", edge="{m["edge"]}", bounds="-30 -10 40 70", steps="2 0.5 2", times="0.5 0.5 0.5")\n'
            )
            self.content += self.tab + self.tab + f"yield from mvr({motor}, 5)\n"

            ####################################
            # move to correct height and pitch #
            ####################################
            if m["method"].lower() == "automatic":
                user_ns["ga"].automatic = True
                self.content += self.tab + f'yield from ga.auto_align(pitch={m["angle"]})\n'
            else:
                if m["sampley"] is not None:
                    if self.check_limit(user_ns["xafs_y"], m["sampley"]) is False:
                        return False
                    self.content += self.tab + f'yield from mv({motor}, {m["sampley"]})\n'
                if m["samplep"] is not None:
                    if self.check_limit(user_ns["xafs_pitch"], m["samplep"]) is False:
                        return False
                    self.content += self.tab + f'yield from mv(xafs_pitch, {m["samplep"]})\n'
                user_ns["ga"].automatic = False

            ############################################################
            # measure XAFS, then return to 0 pitch and close all plots #
            ############################################################
            self.content += self.tab + "yield from mvr(xafs_det, -5)\n"
            command = self.tab + "yield from xafs('%s.ini'" % self.basename
            for k in m.keys():
                ## skip cells with macro-building parameters that are not INI parameters
                if self.skip_keyword(k):
                    continue
                ## skip element & edge if they are same as default
                elif k in ("element", "edge"):
                    if m[k] == self.measurements[0][k]:
                        continue
                ## skip cells with only whitespace
                if type(m[k]) is str and len(m[k].strip()) == 0:
                    m[k] = None
                ## if a cell has data, put it in the argument list for xafs()
                if m[k] is not None:
                    if k == "filename":
                        fname = self.make_filename(m)
                        command += f", filename='{fname}'"
                    elif type(m[k]) is int:
                        command += ", %s=%d" % (k, m[k])
                    elif type(m[k]) is float:
                        command += ", %s=%.3f" % (k, m[k])
                    else:
                        command += ", %s='%s'" % (k, m[k])
            command += ")\n"
            self.content += command
            if m["method"].lower() == "automatic":
                self.content += self.tab + "yield from mvr(xafs_det, 5)\n"
                self.content += self.tab + "yield from ga.flatten()\n"
                self.content += self.tab + "yield from mvr(xafs_det, -5)\n"
            self.content += self.tab + "close_last_plot()\n\n"

            ########################################
            # approximate time cost of this sample #
            ########################################
            self.estimate_time(m, element, edge)

        if self.nreps > 1:
            self.tab = " " * 8

        if self.close_shutters:
            self.content += self.tab + "if not dryrun:\n"
            self.content += self.tab + "    BMMuser.running_macro = False\n"
            self.content += self.tab + "    BMM_clear_suspenders()\n"
            self.content += self.tab + "    yield from shb.close_plan()\n"

    def get_keywords(self, row, defaultline):
        """Instructions for parsing spreadsheet columns into keywords.

        arguments
        ---------
        row : contents of a row as read by openpyxl, i.e. ws.rows
        defaultline : True only if this row contains the default
        parameters, i.e. the green row

        This must return a dictionary.  The dictionary keys are the
        keywords related to the column labels from the spreadsheet,
        the values are cell contents, possibly reduced to a specific
        type.

        """
        this = {
            "default": defaultline,
            "slot": row[1].value,  # sample location
            "measure": self.truefalse(row[2].value, "measure"),  # filename and visualization
            "filename": str(row[3].value),
            "nscans": row[4].value,
            "start": row[5].value,
            "spin": self.truefalse(row[6].value, "spin"),
            "element": row[7].value,  # energy range
            "edge": row[8].value,
            "focus": row[9].value,
            "angle": row[10].value,
            "sample": self.escape_quotes(str(row[11].value)),  # scan metadata
            "prep": self.escape_quotes(str(row[12].value)),
            "comment": self.escape_quotes(str(row[13].value)),
            "bounds": row[14].value,  # scan parameters
            "steps": row[15].value,
            "times": row[16].value,
            "method": row[17].value,
            "samplep": row[18].value,  # other motors
            "sampley": row[19].value,
            "slitheight": row[20].value,
            "detectorx": row[21].value,
            "snapshots": self.truefalse(row[22].value, "snapshots"),  # flags
            "htmlpage": self.truefalse(row[23].value, "htmlpage"),
            "usbstick": self.truefalse(row[24].value, "usbstick"),
            "bothways": self.truefalse(row[25].value, "bothways"),
            "channelcut": self.truefalse(row[26].value, "channelcut"),
            "ththth": self.truefalse(row[27].value, "ththth"),
            "url": row[28].value,
            "doi": row[29].value,
            "cif": row[30].value,
        }
        return this
