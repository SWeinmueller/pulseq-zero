from dataclasses import dataclass
from ..adapter import Opts, make_delay, make_trapezoid, calc_duration


def make_arbitrary_rf(
    signal,
    flip_angle,
    bandwidth=0,
    delay=0,
    dwell=None,
    freq_offset=0,
    no_signal_scaling=False,
    max_grad=0,
    max_slew=0,
    phase_offset=0,
    return_delay=False,
    return_gz=False,
    slice_thickness=0,
    system=None,
    time_bw_product=0,
    shim_array=None,
    use=str(),
):
    if system is None:
        system = Opts.default
    if dwell is None:
        dwell = system.rf_raster_time
    delay = max(delay, system.rf_dead_time)

    duration = len(signal) * dwell

    rf = Pulse(
        flip_angle,
        duration,
        freq_offset,
        phase_offset,
        delay,
        system.rf_ringdown_time,
        shim_array
    )
    ret_val = (rf, )

    if return_gz:
        if max_grad is None:
            max_grad = system.max_grad
        if max_slew is None:
            max_slew = system.max_slew

        if bandwidth is None:
            bandwidth = time_bw_product / duration
        area = bandwidth / slice_thickness * duration

        gz = make_trapezoid(
            "z", system=system,
            flat_area=area, flat_time=duration
        )

        if rf.delay > gz.rise_time:
            gz.delay = rf.delay - gz.rise_time
        if rf.delay < gz.rise_time + gz.delay:
            rf.delay = gz.rise_time + gz.delay

        ret_val = (*ret_val, gz)

    if return_delay and rf.ringdown_time > 0:
        delay = make_delay(calc_duration(rf) + rf.ringdown_time)
        ret_val = (*ret_val, delay)

    return ret_val


def make_block_pulse(
    flip_angle,
    delay=0,
    duration=None,
    bandwidth=None,
    time_bw_product=0.25,
    freq_offset=0,
    phase_offset=0,
    return_delay=False,
    system=None,
    shim_array=None,
    use="",
):
    if system is None:
        system = Opts.default
    delay = max(delay, system.rf_dead_time)

    if duration is None:
        if bandwidth is None:
            duration = 1e-4
        else:
            duration = time_bw_product / bandwidth
    else:
        assert bandwidth is None

    rf = Pulse(
        flip_angle,
        duration,
        freq_offset,
        phase_offset,
        delay,
        system.rf_ringdown_time,
        shim_array
    )

    if system.rf_dead_time > rf.delay:
        rf.delay = system.rf_dead_time

    if return_delay:
        return (rf, make_delay(calc_duration(rf) + system.rf_ringdown_time))
    else:
        return rf


def make_gauss_pulse(
    flip_angle,
    apodization=0,
    bandwidth=None,
    center_pos=0.5,
    delay=0,
    dwell=0,
    duration=4e-3,
    freq_offset=0,
    max_grad=0,
    max_slew=0,
    phase_offset=0,
    return_gz=False,
    return_delay=False,
    slice_thickness=0,
    system=None,
    time_bw_product=4,
    shim_array=None,
    use=""
):
    if system is None:
        system = Opts.default
    delay = max(delay, system.rf_dead_time)

    rf = Pulse(
        flip_angle,
        duration,
        freq_offset,
        phase_offset,
        delay,
        system.rf_ringdown_time,
        shim_array
    )
    ret_val = (rf, )

    if return_gz:
        if max_grad is None:
            max_grad = system.max_grad
        if max_slew is None:
            max_slew = system.max_slew

        if bandwidth is None:
            bandwidth = time_bw_product / duration
        area = bandwidth / slice_thickness * duration

        gz = make_trapezoid(
            "z", system=system,
            flat_area=area, flat_time=duration
        )
        gzr = make_trapezoid(
            "z", system=system,
            area=-area * (1 - center_pos) - 0.5 * (gz.area - area)
        )

        if rf.delay > gz.rise_time:
            gz.delay = rf.delay - gz.rise_time
        if rf.delay < gz.rise_time + gz.delay:
            rf.delay = gz.rise_time + gz.delay

        ret_val = (*ret_val, gz, gzr)

    if return_delay and rf.ringdown_time > 0:
        delay = make_delay(calc_duration(rf) + rf.ringdown_time)
        ret_val = (*ret_val, delay)

    return ret_val


def make_sinc_pulse(
    flip_angle,
    apodization=0,
    delay=0,
    duration=4e-3,
    dwell=0,
    center_pos=0.5,
    freq_offset=0,
    max_grad=None,
    max_slew=None,
    phase_offset=0,
    return_delay=False,
    return_gz=False,
    slice_thickness=0,
    system=None,
    time_bw_product=4,
    shim_array=None,
    use=""
):
    if system is None:
        system = Opts.default
    delay = max(delay, system.rf_dead_time)

    rf = Pulse(
        flip_angle,
        duration,
        freq_offset,
        phase_offset,
        delay,
        system.rf_ringdown_time,
        shim_array
    )
    ret_val = (rf, )

    if return_gz:
        if max_grad is None:
            max_grad = system.max_grad
        if max_slew is None:
            max_slew = system.max_slew

        BW = time_bw_product / duration
        area = BW / slice_thickness * duration

        gz = make_trapezoid(
            "z", max_grad=max_grad, max_slew=max_slew,
            flat_time=duration, flat_area=area
        )
        gzr = make_trapezoid(
            "z", max_grad=max_grad, max_slew=max_slew,
            area=-area * (1 - center_pos) - 0.5 * (gz.area - area)
        )

        if rf.delay > gz.rise_time:
            gz.delay = rf.delay - gz.rise_time
        if rf.delay < gz.rise_time + gz.delay:
            rf.delay = gz.rise_time + gz.delay

        ret_val = (*ret_val, gz, gzr)

    if return_delay and rf.ringdown_time > 0:
        delay = make_delay(rf.duration)
        ret_val = (*ret_val, delay)

    return ret_val


@dataclass
class Pulse:
    flip_angle: ...
    shape_dur: ...
    freq_offset: ...  # ignored by sim
    phase_offset: ...
    delay: ...
    ringdown_time: ...  # important for duration
    shim_array: ... # requres rfshim pulseq in pulseq mode

    @property
    def duration(self):
        return self.delay + self.shape_dur + self.ringdown_time
