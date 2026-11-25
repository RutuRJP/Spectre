# Learning-Based Detection of Spectre Side-Channel Attacks

## 1. Overview

Spectre is a class of microarchitectural attacks that exploits speculative execution in modern processors to leak sensitive information across security boundaries. By manipulating branch prediction, an attacker can induce speculative memory accesses that leave observable traces in the CPU cache, even after the speculative execution is rolled back.

This project investigates the detection of **Spectre Variant-1 (Bounds Check Bypass)** attacks using Hardware Performance Counters (HPCs) and Machine Learning.

We first reproduce a Spectre Variant-1 proof-of-concept attack to understand its microarchitectural behavior. We then collect hardware performance statistics during attack and benign workload executions to identify distinguishing execution patterns.

Our primary objective is to develop a multi-feature, machine learning-based detection framework that can identify suspicious speculative execution behavior without requiring modifications to CPU hardware.

## 2. Objectives

The major objectives of this project are:

- Understand and reproduce the Spectre Variant-1 speculative execution attack.
- Analyze cache-based side-channel leakage and branch misprediction behavior.
- Collect microarchitectural execution statistics using Linux Hardware Performance Counters.
- Identify distinguishing patterns between malicious and benign workloads.
- Develop a machine learning-based framework for detecting Spectre-style attacks.
- Investigate the feasibility of lightweight runtime monitoring and complementary defensive mechanisms.

## 3. System Architecture

The proposed framework consists of the following stages:

```text
       Spectre Variant-1 PoC
                |
                v
       Microarchitectural
       Execution Behavior
                |
                v
       Hardware Performance
       Counter Collection
           (Linux perf)
                |
                v
        Feature Extraction
                |
                v
         Dataset Creation
                |
                v
       Machine Learning Model
       (RF / SVM / Logistic
           Regression)
                |
                v
        Attack Classification
          Attack / Normal
                |
                v
       Detection and Analysis
```

### Detection Features

The following hardware performance metrics are currently monitored:

| Feature | Description |
|---|---|
| `cycles` | Total processor cycles |
| `instructions` | Total instructions executed |
| `branches` | Total branch instructions |
| `branch-misses` | Number of branch mispredictions |
| `cache-references` | Cache references recorded |
| `cache-misses` | Number of cache misses |

Additional derived features include:

- Instructions Per Cycle (IPC)
- Branch Miss Rate
- Cache Miss Rate

## 4. Implementation Details

### 4.1 Spectre Attack Implementation

The project uses a publicly available SpectrePoC implementation to reproduce the Spectre Variant-1 attack.

The attack follows these steps:

1. **Branch Predictor Training:** Repeatedly execute the victim function with valid array indices to train the branch predictor.
2. **Malicious Index Injection:** Supply an out-of-bounds index to trigger incorrect speculative execution.
3. **Speculative Secret Access:** The processor speculatively accesses sensitive memory.
4. **Cache Encoding:** The secret value influences the cache state through a probe array.
5. **Timing Measurement:** Measure cache access latency to infer the secret value.

### 4.2 Performance Monitoring

Linux `perf` is used to collect hardware performance counter statistics.

Example command:

```bash
perf stat -x , -e cycles,instructions,branches,branch-misses,cache-references,cache-misses ./spectre.out
```

The same monitoring procedure is applied to benign workloads to establish a comparative baseline.

### 4.3 Benign Workloads

Three benign workloads are currently used for comparison:

- **Matrix Multiplication:** Evaluates computationally intensive operations.
- **Branch Stress:** Evaluates branch-intensive execution behavior.
- **Memory Test:** Evaluates memory-intensive execution patterns.

These workloads help assess whether the observed microarchitectural characteristics are specific to Spectre or can also occur during legitimate program execution.

### 4.4 Machine Learning Detection

The collected performance counter statistics are converted into structured feature vectors for machine learning analysis.

The planned classification models include:

- Logistic Regression
- Random Forest
- Support Vector Machine (SVM)

The models will be compared using standard classification metrics, including accuracy, precision, recall, F1-score, and false positive rate.

## 5. Experimental Progress

### Completed Work

- Successfully reproduced the Spectre Variant-1 proof-of-concept attack.
- Verified secret extraction through cache timing measurements.
- Configured Linux hardware performance counter monitoring using `perf`.
- Implemented three benign comparison workloads.
- Developed a Python-based pipeline for parsing performance counter outputs and generating structured datasets.
- Collected an initial dataset containing 123 samples.

### Preliminary Experimental Results

The initial dataset contains:

| Category | Samples |
|---|---:|
| Attack | 68 |
| Normal | 55 |
| **Total** | **123** |

Representative performance statistics:

| Workload | IPC | Branch Miss (%) | Cache Miss (%) |
|---|---:|---:|---:|
| Spectre PoC | 0.44 | 0.93 | 63.57 |
| Matrix Multiply | 1.82 | 0.21 | 0.06 |
| Branch Stress | 2.23 | 0.30 | 13.51 |
| Memory Test | 2.68 | 0.01 | 69.80 |

The preliminary measurements indicate that Spectre execution exhibits distinctive microarchitectural characteristics.

However, the memory-intensive workload also exhibits a high cache miss rate, demonstrating that cache miss rate alone is insufficient for reliable attack detection. This motivates the use of multiple performance features and machine learning-based classification.

**Note:** The current dataset uses an initial cache-miss-rate-based labeling heuristic. Ground-truth labeling, broader workload coverage, and repeated experimental validation are part of the ongoing work. The current measurements should therefore be considered preliminary rather than validated detection performance.

## 6. Planned Work

The next phase of the project focuses on improving detection reliability and moving towards a practical monitoring prototype.

Planned extensions include:

1. **Dataset Expansion:** Collect execution traces across additional benign workloads, including cryptographic computations, database operations, and network services.
2. **Feature Expansion:** Incorporate additional hardware events such as L1 cache misses, last-level cache misses, and TLB misses, where supported.
3. **ML Model Development:** Train and compare Logistic Regression, Random Forest, and SVM classifiers.
4. **Robust Evaluation:** Evaluate models using stratified train-test splits, cross-validation, and standard classification metrics.
5. **Mitigation-Aware Analysis:** Investigate detection behavior under selected Spectre mitigation configurations.
6. **Real-Time Monitoring:** Develop a lightweight monitoring prototype using the Linux `perf_event_open` interface to assess detection latency and runtime overhead.

## 7. Technology Stack

- **Programming Languages:** C, Python
- **Operating System:** Linux / Ubuntu
- **Performance Monitoring:** Linux `perf`, Hardware Performance Counters
- **Machine Learning:** Scikit-learn
- **Data Processing:** Pandas, NumPy
- **Compiler:** GCC
- **Security Domain:** Microarchitectural Security, Speculative Execution, Cache Side-Channel Attacks

## 8. Getting Started

### Prerequisites

- Linux-based environment
- GCC compiler
- Linux `perf` utility
- Python 3
- Required Python libraries for dataset processing and machine learning

### Step 1: Clone the Repository

```bash
git clone https://github.com/RutuRJP/Spectre
cd Spectre
```

### Step 2: Compile the Spectre PoC

Navigate to the Spectre implementation directory and compile the source code.

```bash
make
```

Alternatively, if compiling manually:

```bash
gcc -O2 -o spectre.out spectre.c
```

*Note: The exact compilation command depends on the source files and build configuration.*

### Step 3: Execute the Spectre PoC

```bash
./spectre.out
```

### Step 4: Collect Performance Counter Statistics

```bash
perf stat -e cycles,instructions,branches,branch-misses,cache-references,cache-misses ./spectre.out
```

### Step 5: Process the Collected Data

Run the Python data-processing scripts to parse the performance counter outputs, extract derived features, and generate the dataset.

*Refer to the respective script files for execution instructions.*

## 9. Project Contributors

**Ruturaj Kamalakar Pol**  
M.Tech Cybersecurity, IIT Delhi

**Sarthak Thapliyal**  
M.Tech Cybersecurity, IIT Delhi

## 10. Disclaimer

The Spectre proof-of-concept is used in a controlled experimental environment to understand microarchitectural vulnerabilities and investigate potential detection mechanisms. It should not be used to access or extract information from systems without explicit authorization.

---

**Keywords:** Spectre, Spectre Variant-1, Speculative Execution, Side-Channel Attacks, Hardware Performance Counters, Machine Learning, Runtime Detection, Systems Security.
