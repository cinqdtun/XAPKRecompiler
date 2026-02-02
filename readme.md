# XAPK Recompiler

Python tool to decompile, patch, and recompile XAPK files. Designed for security analysis, it automates **network traffic sniffing configuration** and **patched binary deployment**.

## Prerequisites

* **Linux Environment**
* **Python 3.x**
* **Java JDK** (Required for APKTool and apksigner)

## Setup

1.  **Install Dependencies**
    Run the setup script to download necessary tools and libraries:
    ```bash
    chmod +x dependencies_linux.sh
    ./dependencies_linux.sh
    ```

2.  **Verify Java**
    Ensure Java JDK is installed and in your PATH:
    ```bash
    java -version
    ```

## Usage

```bash
python main.py <input_xapk> [options]
```

### Arguments

| Argument | Description |
| --- | --- |
| `input_xapk` | **Required.** Path to the target XAPK file. |
| `--network-fix` | Injects a network security configuration to allow app traffic analysis. |
| `--extract-native-libs` | Sets `extractNativeLibs="true"` in the manifest (fixes loading issues). |
| `--pause` | Pauses execution after patching but before rebuilding. Allows for manual file modification. |
| `--install` | Installs the patched APK to a connected ADB device after rebuilding. |

### Examples

**Basic patch:**

```bash
python main.py game.xapk --network-fix
```

**Patch, fix libs, and install to device:**

```bash
python main.py app.xapk --network-fix --extract-native-libs --install
```

## Cleanup

To remove temporary build directories and artifacts:

```bash
chmod +x clean.sh
./clean.sh
```
