import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks



def detect_intervals_find_peaks(signal, t, th_on, th_off):
    """
    Detect ON/OFF events using find_peaks on a voltage signal.
    Returns arrays of boolean flags (like e_** columns) at each time point.
    
    Strategy:
      - Find peaks (local maxima) above th_on  → these are "ON" transitions
      - Find troughs (local minima) below th_off → these are "OFF" transitions
    """
    # peak_distance = max(1, len(signal) // 500)  # adaptive minimum distance

    # Detect peaks (ON events)
    peaks, _ = find_peaks(signal, height=th_on, distance=2000)

    # Detect troughs (OFF events) — invert signal
    inv_signal = -signal
    th_inv = -th_off
    troughs, _ = find_peaks(inv_signal, height=th_inv, distance=2000)

    # Build boolean arrays aligned to t
    e_on  = np.zeros(len(t), dtype=bool)
    e_off = np.zeros(len(t), dtype=bool)
    e_on[peaks]   = True
    e_off[troughs] = True

    return e_on, e_off, peaks, troughs


def compute_intervals(e_on_flags, e_off_flags, t):
    """
    Given boolean ON/OFF flag arrays, extract (start_time, end_time, duration) 
    for each detected interval.
    """
    on_times  = t[e_on_flags]
    off_times = t[e_off_flags]
    intervals = []
    for on_t in on_times:
        # Find the next OFF event after this ON
        candidates = off_times[off_times > on_t]
        if len(candidates) > 0:
            off_t = candidates[0]
            intervals.append((on_t, off_t, off_t - on_t))
    return intervals  # list of (start, end, duration)


def compare_intervals(gt_intervals, det_intervals, tol=0.05):
    """
    Compare detected intervals against ground truth.
    A detection is "correct" if:
      - Its start time is within `tol` seconds of a GT start, AND
      - Its end   time is within `tol` seconds of the corresponding GT end.
    
    Returns:
      matched pairs, false positives, false negatives, accuracy %, duration errors
    """
    matched = []
    used_gt  = set()
    used_det = set()

    for di, (ds, de, dd) in enumerate(det_intervals):
        for gi, (gs, ge, gd) in enumerate(gt_intervals):
            if gi in used_gt:
                continue
            if abs(ds - gs) <= tol and abs(de - ge) <= tol:
                matched.append((gi, di, gs, ge, ds, de))
                used_gt.add(gi)
                used_det.add(di)
                break

    false_negatives = [gt_intervals[i] for i in range(len(gt_intervals)) if i not in used_gt]
    false_positives  = [det_intervals[i] for i in range(len(det_intervals)) if i not in used_det]

    total_gt  = len(gt_intervals)
    precision = len(matched) / len(det_intervals) * 100 if det_intervals else 0.0
    recall    = len(matched) / total_gt * 100            if total_gt     else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)

    duration_errors = []
    for (gi, di, gs, ge, ds, de) in matched:
        gt_dur  = gt_intervals[gi][2]
        det_dur = det_intervals[di][2]
        duration_errors.append(abs(gt_dur - det_dur) / gt_dur * 100 if gt_dur > 0 else 0.0)

    return {
        "matched":          matched,
        "false_positives":  false_positives,
        "false_negatives":  false_negatives,
        "precision_pct":    precision,
        "recall_pct":       recall,
        "f1_score":         f1,
        "n_gt":             total_gt,
        "n_detected":       len(det_intervals),
        "n_matched":        len(matched),
        "mean_dur_err_pct": np.mean(duration_errors) if duration_errors else np.nan,
        "std_dur_err_pct":  np.std(duration_errors)  if duration_errors else np.nan,
    }


def print_accuracy_report(label, stats):
    print(f"\n{'='*55}")
    print(f"  Accuracy report — {label}")
    print(f"{'='*55}")
    print(f"  Ground-truth intervals  : {stats['n_gt']}")
    print(f"  Detected  intervals     : {stats['n_detected']}")
    print(f"  Correctly matched       : {stats['n_matched']}")
    print(f"  False positives         : {len(stats['false_positives'])}")
    print(f"  False negatives         : {len(stats['false_negatives'])}")
    print(f"  Precision               : {stats['precision_pct']:.1f} %")
    print(f"  Recall                  : {stats['recall_pct']:.1f} %")
    print(f"  F1 score                : {stats['f1_score']:.1f} %")
    print(f"  Mean duration error     : {stats['mean_dur_err_pct']:.2f} %")
    print(f"  Std  duration error     : {stats['std_dur_err_pct']:.2f} %")
    print(f"{'='*55}")


def plot_invariant(filename, th_lo_per, th_up_per):
    start = 10000
    end   = -1

    dataset = pd.read_csv(filename, delimiter=' ', header=3)
    data    = dataset.values

    t      = np.array([x / 1000000 for x in data[start:end, 0]])
    c      = data[start:end, 1]
    v_pd   = data[start:end, 2]
    v_lp   = data[start:end, 3]
    e_pd     = data[start:end, 4].astype(bool)
    e_pd_end = data[start:end, 5].astype(bool)
    e_lp     = data[start:end, 6].astype(bool)
    e_lp_end = data[start:end, 7].astype(bool)

    first_interval  = [x / 1000 for x in data[start:end, 8]]
    second_interval = [x / 1000 for x in data[start:end, 9]]

    # ── Thresholds (same logic as original) ─────────────────────────────────
    th_up_lp = np.min(v_lp) + (np.max(v_lp) - np.min(v_lp)) * th_up_per
    th_lo_lp = np.min(v_lp) + (np.max(v_lp) - np.min(v_lp)) * 0.4

    th_up_pd = np.min(v_pd) + (np.max(v_pd) - np.min(v_pd)) * 0.4
    th_lo_pd = np.min(v_pd) + (np.max(v_pd) - np.min(v_pd)) * th_lo_per

    # ── find_peaks detection ────────────────────────────────────────────────
    fp_e_lp, fp_e_lp_end, lp_peaks, lp_troughs = detect_intervals_find_peaks(
        v_lp, t, th_on=th_up_lp, th_off=th_lo_lp)

    fp_e_pd, fp_e_pd_end, pd_peaks, pd_troughs = detect_intervals_find_peaks(
        v_pd, t, th_on=th_up_pd, th_off=th_lo_pd)

    # ── Ground-truth intervals ───────────────────────────────────────────────
    gt_intervals_lp  = compute_intervals(e_lp,     e_lp_end,     t)
    gt_intervals_pd  = compute_intervals(e_pd,     e_pd_end,     t)

    # ── Detected intervals ───────────────────────────────────────────────────
    det_intervals_lp = compute_intervals(fp_e_lp,  fp_e_lp_end,  t)
    det_intervals_pd = compute_intervals(fp_e_pd,  fp_e_pd_end,  t)

    # ── Accuracy comparison ──────────────────────────────────────────────────
    tol = (t[-1] - t[0]) * 0.01   # 1 % of total time window as tolerance
    stats_lp = compare_intervals(gt_intervals_lp, det_intervals_lp, tol=tol)
    stats_pd = compare_intervals(gt_intervals_pd, det_intervals_pd, tol=tol)

    print_accuracy_report("LP signal", stats_lp)
    print_accuracy_report("PD signal", stats_pd)

    # ── Duration arrays for plotting ─────────────────────────────────────────
    def durations_at_t(intervals, t):
        """Return duration value at the ON timestamp, NaN elsewhere."""
        dur = np.full(len(t), np.nan)
        for (s, e, d) in intervals:
            idx = np.searchsorted(t, s)
            if idx < len(t):
                dur[idx] = d
        return dur

    gt_dur_lp  = durations_at_t(gt_intervals_lp,  t)
    det_dur_lp = durations_at_t(det_intervals_lp, t)
    gt_dur_pd  = durations_at_t(gt_intervals_pd,  t)
    det_dur_pd = durations_at_t(det_intervals_pd, t)

    # ════════════════════════════════════════════════════════════════════════
    # FIGURE 1 — Original view (unchanged)
    # ════════════════════════════════════════════════════════════════════════
    fig1, axes1 = plt.subplots(5, 1, figsize=(14, 12), sharex=True)
    fig1.suptitle("Original signal view", fontsize=13, fontweight='bold')

    # LP voltage
    axes1[0].set_ylabel("Voltage LP (V)")
    axes1[0].plot(t, v_lp, lw=0.8)
    on_ev  = t[e_lp];     axes1[0].plot(on_ev,  np.ones_like(on_ev)*np.max(v_lp),  '.', ms=8, color='green', label='GT ON')
    off_ev = t[e_lp_end]; axes1[0].plot(off_ev, np.ones_like(off_ev)*np.max(v_lp), '.', ms=8, color='red',   label='GT OFF')
    axes1[0].axhline(th_up_lp, ls='--', color='purple', label='th_up')
    axes1[0].axhline(th_lo_lp, ls='--', color='black',  label='th_low')
    axes1[0].legend(fontsize=7)

    # PD voltage
    axes1[1].set_ylabel("Voltage PD (V)")
    axes1[1].plot(t, v_pd, lw=0.8)
    on_ev  = t[e_pd];     axes1[1].plot(on_ev,  np.ones_like(on_ev)*np.max(v_pd),  '.', ms=8, color='green', label='GT ON')
    off_ev = t[e_pd_end]; axes1[1].plot(off_ev, np.ones_like(off_ev)*np.max(v_pd), '.', ms=8, color='red',   label='GT OFF')
    axes1[1].axhline(th_up_pd, ls='--', color='black',  label='th_up_per')
    axes1[1].axhline(th_lo_pd, ls='--', color='purple', label='th_low_per')
    axes1[1].legend(fontsize=7)

    axes1[2].set_ylabel("Current (nA)"); axes1[2].plot(t, c, lw=0.8)
    axes1[3].set_ylabel("1st interval (s)"); axes1[3].plot(t, first_interval, lw=0.8)
    axes1[4].set_ylabel("2nd interval (s)"); axes1[4].plot(t, second_interval, lw=0.8)
    axes1[4].set_xlabel("Time (s)")
    plt.tight_layout()

    # ════════════════════════════════════════════════════════════════════════
    # FIGURE 2 — Signal + Ground Truth vs find_peaks (LP)
    # ════════════════════════════════════════════════════════════════════════
    fig2, axes2 = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig2.suptitle(
        f"LP Signal — Ground Truth vs find_peaks  |  "
        f"Precision {stats_lp['precision_pct']:.1f}%  "
        f"Recall {stats_lp['recall_pct']:.1f}%  "
        f"F1 {stats_lp['f1_score']:.1f}%",
        fontsize=12, fontweight='bold')

    # Raw signal
    axes2[0].set_ylabel("Voltage LP (V)")
    axes2[0].plot(t, v_lp, lw=0.8, color='steelblue', label='Signal')
    axes2[0].axhline(th_up_lp, ls='--', color='purple', alpha=0.6, label='th_up')
    axes2[0].axhline(th_lo_lp, ls='--', color='black',  alpha=0.6, label='th_lo')
    axes2[0].legend(fontsize=8)

    # Experiment detections
    axes2[1].set_ylabel("Experiment detections\nevent markers")
    axes2[1].plot(t, v_lp, lw=0.5, color='steelblue', alpha=0.4)
    on_ev  = t[e_lp];     axes2[1].vlines(on_ev,  0, 1, transform=axes2[1].get_xaxis_transform(), color='green', lw=1, label='Experiment ON')
    off_ev = t[e_lp_end]; axes2[1].vlines(off_ev, 0, 1, transform=axes2[1].get_xaxis_transform(), color='red',   lw=1, label='Experiment OFF')
    # shade GT intervals
    for (s, e_, d) in gt_intervals_lp:
        axes2[1].axvspan(s, e_, alpha=0.15, color='green')
    axes2[1].legend(fontsize=8)

    # find_peaks detections
    axes2[2].set_ylabel("find_peaks\ndetection")
    axes2[2].plot(t, v_lp, lw=0.5, color='steelblue', alpha=0.4)
    on_fp  = t[fp_e_lp];     axes2[2].vlines(on_fp,  0, 1, transform=axes2[2].get_xaxis_transform(), color='limegreen', lw=1, label='findpeaks ON')
    off_fp = t[fp_e_lp_end]; axes2[2].vlines(off_fp, 0, 1, transform=axes2[2].get_xaxis_transform(), color='tomato',    lw=1, label='findpeaks OFF')
    for (s, e_, d) in det_intervals_lp:
        axes2[2].axvspan(s, e_, alpha=0.15, color='limegreen')
    axes2[2].legend(fontsize=8)
    axes2[2].set_xlabel("Time (s)")
    plt.tight_layout()

    # ════════════════════════════════════════════════════════════════════════
    # FIGURE 3 — Signal + Ground Truth vs find_peaks (PD)
    # ════════════════════════════════════════════════════════════════════════
    fig3, axes3 = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig3.suptitle(
        f"PD Signal — Ground Truth vs find_peaks  |  "
        f"Precision {stats_pd['precision_pct']:.1f}%  "
        f"Recall {stats_pd['recall_pct']:.1f}%  "
        f"F1 {stats_pd['f1_score']:.1f}%",
        fontsize=12, fontweight='bold')

    axes3[0].set_ylabel("Voltage PD (V)")
    axes3[0].plot(t, v_pd, lw=0.8, color='darkorange', label='Signal')
    axes3[0].axhline(th_up_pd, ls='--', color='black',  alpha=0.6, label='th_up')
    axes3[0].axhline(th_lo_pd, ls='--', color='purple', alpha=0.6, label='th_lo')
    axes3[0].legend(fontsize=8)

    axes3[1].set_ylabel("Ground Truth\nevent markers")
    axes3[1].plot(t, v_pd, lw=0.5, color='darkorange', alpha=0.4)
    on_ev  = t[e_pd];     axes3[1].vlines(on_ev,  0, 1, transform=axes3[1].get_xaxis_transform(), color='green', lw=1, label='GT ON')
    off_ev = t[e_pd_end]; axes3[1].vlines(off_ev, 0, 1, transform=axes3[1].get_xaxis_transform(), color='red',   lw=1, label='GT OFF')
    for (s, e_, d) in gt_intervals_pd:
        axes3[1].axvspan(s, e_, alpha=0.15, color='green')
    axes3[1].legend(fontsize=8)

    axes3[2].set_ylabel("find_peaks\ndetection")
    axes3[2].plot(t, v_pd, lw=0.5, color='darkorange', alpha=0.4)
    on_fp  = t[fp_e_pd];     axes3[2].vlines(on_fp,  0, 1, transform=axes3[2].get_xaxis_transform(), color='limegreen', lw=1, label='FP ON')
    off_fp = t[fp_e_pd_end]; axes3[2].vlines(off_fp, 0, 1, transform=axes3[2].get_xaxis_transform(), color='tomato',    lw=1, label='FP OFF')
    for (s, e_, d) in det_intervals_pd:
        axes3[2].axvspan(s, e_, alpha=0.15, color='limegreen')
    axes3[2].legend(fontsize=8)
    axes3[2].set_xlabel("Time (s)")
    plt.tight_layout()

    # # ════════════════════════════════════════════════════════════════════════
    # # FIGURE 4 — Interval duration comparison (GT vs find_peaks)
    # # ════════════════════════════════════════════════════════════════════════
    # fig4, axes4 = plt.subplots(2, 2, figsize=(14, 8))
    # fig4.suptitle("Interval duration comparison — Ground Truth vs find_peaks",
    #               fontsize=13, fontweight='bold')

    # def scatter_durations(ax, gt_intervals, det_intervals, stats, label):
    #     gt_durs  = [d for (_, _, d) in gt_intervals]
    #     det_durs = [d for (_, _, d) in det_intervals]
    #     # scatter matched pairs
    #     matched_gt  = [gt_intervals[m[0]][2]  for m in stats['matched']]
    #     matched_det = [det_intervals[m[1]][2] for m in stats['matched']]
    #     ax.scatter(matched_gt, matched_det, s=30, alpha=0.7, color='steelblue', label='Matched pairs')
    #     # identity line
    #     all_durs = matched_gt + matched_det
    #     if all_durs:
    #         lo, hi = min(all_durs), max(all_durs)
    #         ax.plot([lo, hi], [lo, hi], 'k--', lw=1, label='Perfect match')
    #     ax.set_xlabel("GT duration (s)")
    #     ax.set_ylabel("Detected duration (s)")
    #     ax.set_title(f"{label}\nPrec={stats['precision_pct']:.1f}%  Rec={stats['recall_pct']:.1f}%  "
    #                  f"F1={stats['f1_score']:.1f}%  ΔDur={stats['mean_dur_err_pct']:.2f}%")
    #     ax.legend(fontsize=8)

    # def timeline_durations(ax, gt_intervals, det_intervals, t, label, color_gt, color_det):
    #     gt_t   = [s for (s, _, _) in gt_intervals]
    #     gt_d   = [d for (_, _, d) in gt_intervals]
    #     det_t  = [s for (s, _, _) in det_intervals]
    #     det_d  = [d for (_, _, d) in det_intervals]
    #     ax.stem(gt_t,  gt_d,  linefmt=color_gt+'-',  markerfmt=color_gt+'o',  basefmt=' ', label='GT duration')
    #     ax.stem(det_t, det_d, linefmt=color_det+'--', markerfmt=color_det+'^', basefmt=' ', label='Detected duration')
    #     ax.set_ylabel("Duration (s)")
    #     ax.set_xlabel("Time (s)")
    #     ax.set_title(f"{label} — duration timeline")
    #     ax.legend(fontsize=8)

    # scatter_durations(axes4[0, 0], gt_intervals_lp,  det_intervals_lp,  stats_lp,  "LP")
    # scatter_durations(axes4[0, 1], gt_intervals_pd,  det_intervals_pd,  stats_pd,  "PD")
    # # timeline_durations(axes4[1, 0], gt_intervals_lp, det_intervals_lp, t, "LP", 'C0', 'C1')
    # timeline_durations(axes4[1, 1], gt_intervals_pd, det_intervals_pd, t, "PD", 'C2', 'C3')

    plt.tight_layout()
    plt.show()


# ── Entry point ─────────────────────────────────────────────────────────────
filename = ""
if len(sys.argv) < 2:
    print("Filename missing!")
    sys.exit()
else:
    filename = sys.argv[1]

file        = open(filename, 'r')
line        = file.readline()
second_line = file.readline()
file.close()

parts     = second_line.split()
th_lo_per = float(parts[1])
th_up_per = float(parts[3])

line = line.strip('\n')
if line == "0":
    print("Single neuron experiment")
    plot_single(filename)
elif line == "1":
    print("Invariant experiment")
    plot_invariant(filename, th_lo_per, th_up_per)
else:
    print("Unknown type of experiment.")
    sys.exit()