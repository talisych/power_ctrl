# Power control
    A Python script to access Smart Power 8H power switch and Cloud AW-2401.
    This mimics web access because we don't know how to use API interface.
    For now, this library only supports turn on/off directly via http interface.

# Build a executable file.
``` bash
pyinstaller -F power_ctrl_cli.py -i if_power_2561374.ico
```
