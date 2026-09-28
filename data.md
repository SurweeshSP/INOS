# Data Directory Overview

This document provides an overview of the `data` directory and its nested structure, along with metadata about the file types and an analysis of the code scripts used for data loading and processing.

## Detailed Folder Structure & Alignment

The `data` folder contains the following sub-directories. Here is a detailed breakdown of how files are organized inside each:

### 1. `dynamic`

- **Structure**: Flat directory.
- **Contents**: Contains 21 `.txt` files. Likely used for storing dynamic input variables or text-based configurations.

### 2. `isomorph`

- **Structure**: Flat directory.
- **Contents**: Contains only `data.py`. This script pulls the dataset from Hugging Face.

### 3. `logior`

- **Structure**: Flat directory.
- **Contents**: Contains only `data.py`. This script pulls the LogiOR dataset from Hugging Face.

### 4. `miplib`

- **Structure**: Flat directory.
- **Contents**: Contains 240 `.gz` compressed archive files. These are likely compressed MIP (Mixed Integer Programming) instances.

### 5. `netlib`

- **Structure**: Flat directory (before execution).
- **Contents**: Contains only `data.py`.
- **Execution Alignment**: When `data.py` is run, it generates a new structure at the project root: `datasets/netlib/raw` (for downloaded instances) and `datasets/netlib/mps` (for decoded `.mps` files).

### 6. `qplib`

- **Structure**: Deeply nested and highly structured.
- **Alignment**:
  - `qplib/qplib/html/`: Contains the bulk of the data, including 457 `.html` files for documentation/viewing.
  - Subdirectories under `html/` organize the optimization models by format:
    - `/gdx/`: 445 GAMS Data eXchange (`.gdx`) files.
    - `/gms/`: 453 GAMS Model (`.gms`) files.
    - `/lp/`: 453 Linear Programming (`.lp`) files.
    - `/mod/`: 453 AMPL/MathProg (`.mod`) files.
    - `/qplib/`: 453 QPLIB specific (`.qplib`) files.
    - `/sol/`: 445 Solution (`.sol`) files.
    - `/png/`: 868 Image files, likely plots or matrix sparsity visualisations.
  - Web Asset Subdirectories: Contains `/DataTables/` and `/FixedHeader/` which store `.css`, `.js`, and image assets for the HTML viewer.

## File Type Statistics

The following table summarizes the types of files found recursively inside the `data` folder:

| Extension | Count | Description / Likely Use Case                                           |
|-----------|-------|-------------------------------------------------------------------------|
| `.png`    | 868   | Image files                                                             |
| `.html`   | 457   | HTML documents                                                          |
| `.gms`    | 453   | GAMS Model files (optimization models)                                  |
| `.lp`     | 453   | Linear Programming format files                                         |
| `.mod`    | 453   | AMPL/MathProg model files                                               |
| `.qplib`  | 453   | QPLIB (Quadratic Programming Library) files                             |
| `.gdx`    | 445   | GAMS Data eXchange files                                                |
| `.sol`    | 445   | Solution files                                                          |
| `.gz`     | 240   | Gzip compressed archives                                                |
| `.txt`    | 21    | Plain text documents                                                    |
| `.css`    | 10    | Cascading Style Sheets                                                  |
| `.js`     | 7     | JavaScript files                                                        |
| `.py`     | 3     | Python scripts                                                          |
| `.ttf`    | 3     | TrueType font files                                                     |
| `.bib`    | 2     | BibTeX bibliography files                                               |
| `.csv`    | 1     | Comma-separated values data                                             |
| `.pdf`    | 1     | PDF document                                                            |
| `.solu`   | 1     | Solution file (MIPLIB specific)                                         |
| `.htaccess`| 1    | Apache configuration file                                               |

## Code Analysis

There are three Python scripts (`.py`) used for loading and preparing datasets:

### 1. `data/isomorph/data.py`

**Purpose**: Data Loading
**Description**: A simple script that utilizes the Hugging Face `datasets` library to load the `Isomorph2026/isomorph-supply-chain-benchmark` dataset.

### 2. `data/logior/data.py`

**Purpose**: Data Loading
**Description**: Similar to the isomorph script, this uses the Hugging Face `datasets` library to load the `LabMem012/LogiOR` dataset.

### 3. `data/netlib/data.py`

**Purpose**: Data Download & Compilation Pipeline
**Description**: A comprehensive Python script designed to fetch, compile, and decode the Netlib Linear Programming (LP) dataset.

- **Download**: It fetches raw LP instances from `https://www.netlib.org/lp/data/`.
- **Compilation**: It downloads a C-based decoder (`emps.c`) and compiles it using `gcc` (generating `emps.exe` on Windows or `emps` on Unix).
- **Decoding**: It loops through the downloaded raw instance files and runs the compiled C program to decode them into the standard `.mps` format within the `datasets/netlib/mps` directory.
