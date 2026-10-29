#!/bin/bash
# Build BAG2JP-Online-Setup.exe in the Linux VM.
# 1. NSIS without root: apt-get download nsis nsis-common; dpkg-deb -x each into ~/tools/nsis
# 2. Payload = the clean release folder (here: extracted from the portable zip).
set -e
REL=~/mnt/Dev/Recomp/BAG2JP/releases/v7-online-portable
PAY=~/work/installer/payload
if [ ! -f "$PAY/BAG2JP-online/BAG2JP.exe" ]; then
  mkdir -p "$PAY" && python3 -c "import zipfile; zipfile.ZipFile('$REL/BAG2JP-online.zip').extractall('$PAY')"
fi
cd "$(dirname "$0")"
NSISDIR=~/tools/nsis/usr/share/nsis ~/tools/nsis/usr/bin/makensis -V2 -DPAYLOAD="$PAY/BAG2JP-online" -DOUTDIR="$REL" bag2jp_online.nsi
ls -la "$REL/BAG2JP-Online-Setup.exe"
