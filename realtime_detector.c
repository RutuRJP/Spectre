/*
 * Real-Time Spectre Detection Prototype (Phase 6)
 * =================================================
 * Uses perf_event_open() to monitor hardware performance counters
 * in real-time, periodically sampling and classifying behaviour.
 *
 * Compile: gcc -O2 -o realtime_detector realtime_detector.c -lm
 * Usage:   ./realtime_detector <PID> [interval_ms]
 *
 * Default interval: 100ms
 * Output: Per-window classification (normal/suspicious)
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>
#include <math.h>
#include <sys/ioctl.h>
#include <sys/syscall.h>
#include <linux/perf_event.h>
#include <linux/hw_breakpoint.h>

/* ──────────── Perf event helpers ──────────── */

static long perf_event_open(struct perf_event_attr *hw_event, pid_t pid,
                            int cpu, int group_fd, unsigned long flags)
{
    return syscall(__NR_perf_event_open, hw_event, pid, cpu, group_fd, flags);
}

static int open_counter(pid_t pid, int type, int config, int group_fd)
{
    struct perf_event_attr pe;
    memset(&pe, 0, sizeof(pe));
    pe.type           = type;
    pe.size           = sizeof(pe);
    pe.config         = config;
    pe.disabled       = 1;
    pe.exclude_kernel = 1;
    pe.exclude_hv     = 1;

    int fd = (int)perf_event_open(&pe, pid, -1, group_fd, 0);
    if (fd == -1) {
        perror("perf_event_open");
    }
    return fd;
}

static long long read_counter(int fd)
{
    long long val = 0;
    if (read(fd, &val, sizeof(val)) != sizeof(val)) {
        perror("read counter");
        return -1;
    }
    return val;
}

/* ──────────── Detection thresholds ──────────── */
/* These are derived from the midterm analysis:
 *   Normal workloads:  IPC ~1.8-2.3,  CMR < 20%,  BMR < 1%
 *   Spectre attacks:   IPC ~0.4-2.7,  CMR > 50%,  BMR ~0.01% or ~0.9%
 *
 * For real-time detection, we use a simple rule-based classifier
 * that mirrors the trained ML model's decision boundaries.
 */
#define CMR_THRESHOLD    40.0   /* Cache miss rate above this = suspicious */
#define IPC_LOW_THRESH   0.6    /* Very low IPC combined with high CMR */

static volatile int running = 1;

void sig_handler(int signo) { running = 0; }

/* ──────────── Simple classification ──────────── */
typedef struct {
    double ipc;
    double bmr;
    double cmr;
    long long cycles;
} features_t;

const char* classify(features_t *f) {
    /* Rule-based classifier inspired by the ML decision boundaries */
    if (f->cmr > CMR_THRESHOLD) {
        return "SPECTRE_SUSPECTED";
    }
    if (f->ipc < IPC_LOW_THRESH && f->cmr > 30.0) {
        return "SPECTRE_SUSPECTED";
    }
    return "NORMAL";
}

/* ──────────── Main ──────────── */
int main(int argc, char *argv[])
{
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <PID> [interval_ms]\n", argv[0]);
        fprintf(stderr, "  PID:         Process ID to monitor\n");
        fprintf(stderr, "  interval_ms: Sampling interval (default: 100)\n");
        return 1;
    }

    pid_t target_pid  = atoi(argv[1]);
    int interval_ms   = (argc >= 3) ? atoi(argv[2]) : 100;

    signal(SIGINT,  sig_handler);
    signal(SIGTERM, sig_handler);

    printf("=== Real-Time Spectre Detection Prototype ===\n");
    printf("Target PID:     %d\n", target_pid);
    printf("Sample interval: %d ms\n", interval_ms);
    printf("Press Ctrl+C to stop\n\n");

    /* Open hardware performance counters */
    int fd_cycles    = open_counter(target_pid, PERF_TYPE_HARDWARE, PERF_COUNT_HW_CPU_CYCLES, -1);
    int fd_instr     = open_counter(target_pid, PERF_TYPE_HARDWARE, PERF_COUNT_HW_INSTRUCTIONS, -1);
    int fd_branches  = open_counter(target_pid, PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_INSTRUCTIONS, -1);
    int fd_br_miss   = open_counter(target_pid, PERF_TYPE_HARDWARE, PERF_COUNT_HW_BRANCH_MISSES, -1);
    int fd_cache_ref = open_counter(target_pid, PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_REFERENCES, -1);
    int fd_cache_miss= open_counter(target_pid, PERF_TYPE_HARDWARE, PERF_COUNT_HW_CACHE_MISSES, -1);

    if (fd_cycles < 0 || fd_instr < 0 || fd_branches < 0 ||
        fd_br_miss < 0 || fd_cache_ref < 0 || fd_cache_miss < 0) {
        fprintf(stderr, "[!] Failed to open perf counters. Check permissions.\n");
        fprintf(stderr, "    Try: sudo sysctl -w kernel.perf_event_paranoid=0\n");
        return 1;
    }

    /* Enable counters */
    ioctl(fd_cycles,    PERF_EVENT_IOC_ENABLE, 0);
    ioctl(fd_instr,     PERF_EVENT_IOC_ENABLE, 0);
    ioctl(fd_branches,  PERF_EVENT_IOC_ENABLE, 0);
    ioctl(fd_br_miss,   PERF_EVENT_IOC_ENABLE, 0);
    ioctl(fd_cache_ref, PERF_EVENT_IOC_ENABLE, 0);
    ioctl(fd_cache_miss,PERF_EVENT_IOC_ENABLE, 0);

    /* Print header */
    printf("%-8s %-12s %-8s %-8s %-12s %s\n",
           "Window", "Cycles", "IPC", "BMR%", "CMR%", "Classification");
    printf("-------------------------------------------------------------\n");

    struct timespec ts;
    ts.tv_sec  = interval_ms / 1000;
    ts.tv_nsec = (interval_ms % 1000) * 1000000L;

    long long prev_cyc = 0, prev_instr = 0, prev_br = 0;
    long long prev_bmiss = 0, prev_cref = 0, prev_cmiss = 0;
    int window = 0;
    int alerts = 0;

    /* Initial read to set baseline */
    prev_cyc   = read_counter(fd_cycles);
    prev_instr = read_counter(fd_instr);
    prev_br    = read_counter(fd_branches);
    prev_bmiss = read_counter(fd_br_miss);
    prev_cref  = read_counter(fd_cache_ref);
    prev_cmiss = read_counter(fd_cache_miss);

    while (running) {
        nanosleep(&ts, NULL);
        window++;

        long long cur_cyc   = read_counter(fd_cycles);
        long long cur_instr = read_counter(fd_instr);
        long long cur_br    = read_counter(fd_branches);
        long long cur_bmiss = read_counter(fd_br_miss);
        long long cur_cref  = read_counter(fd_cache_ref);
        long long cur_cmiss = read_counter(fd_cache_miss);

        if (cur_cyc < 0) break;  /* Process may have ended */

        long long d_cyc   = cur_cyc   - prev_cyc;
        long long d_instr = cur_instr - prev_instr;
        long long d_br    = cur_br    - prev_br;
        long long d_bmiss = cur_bmiss - prev_bmiss;
        long long d_cref  = cur_cref  - prev_cref;
        long long d_cmiss = cur_cmiss - prev_cmiss;

        prev_cyc = cur_cyc; prev_instr = cur_instr; prev_br = cur_br;
        prev_bmiss = cur_bmiss; prev_cref = cur_cref; prev_cmiss = cur_cmiss;

        if (d_cyc <= 0 || d_br <= 0 || d_cref <= 0) continue;

        features_t feat;
        feat.ipc    = (double)d_instr / d_cyc;
        feat.bmr    = (double)d_bmiss / d_br * 100.0;
        feat.cmr    = (double)d_cmiss / d_cref * 100.0;
        feat.cycles = d_cyc;

        const char *result = classify(&feat);
        int is_alert = (strcmp(result, "NORMAL") != 0);
        if (is_alert) alerts++;

        printf("%-8d %-12lld %-8.3f %-8.4f %-12.2f %s%s\n",
               window, d_cyc, feat.ipc, feat.bmr, feat.cmr,
               result, is_alert ? " ⚠" : "");
    }

    printf("\n-------------------------------------------------------------\n");
    printf("Monitoring complete: %d windows, %d alerts\n", window, alerts);

    /* Cleanup */
    close(fd_cycles);
    close(fd_instr);
    close(fd_branches);
    close(fd_br_miss);
    close(fd_cache_ref);
    close(fd_cache_miss);

    return 0;
}
