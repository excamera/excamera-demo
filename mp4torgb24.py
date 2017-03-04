#! /usr/bin/env python
import subprocess
import sys

if len(sys.argv) < 3:
    print "USAGE: mp4torgb24.py input-file output-file"
    sys.exit(1)

subprocess.call("ffmpeg -i {infile} -f rawvideo -vcodec rawvideo -pix_fmt rgb24 {outfile}".format(
        infile=sys.argv[1],
        outfile=sys.argv[2]),
    shell=True)

