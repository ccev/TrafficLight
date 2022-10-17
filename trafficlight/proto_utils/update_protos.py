"""
This script will automatically create or update a compiled PogoProtos module for Python.
Make sure to run it from within your project directory.
If you run it, it's going to:
- Create a `protos` directoy
- Create a `pogo.proto` file
- Fill this directoy with an `__init__.py`, `pogo_pb2.py` and a `pogo_pb2.pyi` file
Using PogoProtos in your project is very easy once you ran this script.
        >>> import protos
        >>> import base64
        >>> protos.GetMapObjectsOutProto.FromString(base64.b64decode("encoded raw"))
# Requirements
1. Install protoc https://github.com/protocolbuffers/protobuf/releases
2. Install required packages for generating the stub file: pip install mypy-protobuf types-protobuf mypy
3. Step 2 installed a protoc-gen-mypy script in your Python/bin (or Python/Scripts in Win) directory. Make sure this
   command is in your PATH.
You should now be able to run this script (python update_protos.py)
# Autocomplete Protos
I found that VS Code works without any further configuration. I have the default Python extension and mypy installed.
For PyCharm you'll need to increase the idea.max.intellisense.filesize property.
Go to Help -> Edit Custom Properties... and put this in:
        idea.max.intellisense.filesize=3500
Note that this might make your IDE slower and increase memory usage. Default is 2500kb. As of writing this, you'll need
at least 3150kb.
"""
#from urllib.request import urlopen
from subprocess import run
import os


if not os.path.isdir("../../protos"):
    print("Creating protos directoy")
    os.mkdir("../../protos")

if not os.path.isfile("../../protos/__init__.py"):
    print("Creating __init__.py file")
    with open("../../protos/__init__.py", "w+", encoding="utf-8") as f:
        f.write("from .pogo_pb2 import *\n")

'''
with urlopen("https://raw.githubusercontent.com/Furtif/POGOProtos/master/base/vbase.proto") as response:
    with open("pogo.proto", "w+", encoding="utf-8") as f:
        f.write(response.read().decode())
    print("Saved pogo.proto file")
'''

run("protoc pogo.proto --python_out=../../protos --mypy_out=../../protos")