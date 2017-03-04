#! /usr/bin/env python
import math
import os
import multiprocessing
import subprocess
import sys

def make_chunk(args):
    filename, dirname, offset, size, idx = args
    with open(filename, "rb") as infile:
        infile.seek(offset)
        with open(os.path.join(dirname, "{0}{1}.raw".format(filename.split(".")[0], str(idx).zfill(5))), "wb") as outfile:
            outfile.write(infile.read(size))

def main(filename, dirname, nframes, w, h, bbp):
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    
    filesize = os.stat(filename).st_size
    chunksize = int(w) * int(h) * int(bbp) * int(nframes)
    
    arglist = [(filename, dirname, offset, chunksize, offset / chunksize) 
                    for offset in range(0, filesize - (filesize % chunksize), chunksize)]
    if filesize % chunksize != 0:
        offset = filesize - (filesize % chunksize)
        arglist.append((filename, dirname, offset, filesize % chunksize, offset / chunksize))
    
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    pool.map(make_chunk, arglist)

    """
    with open(filename, "rb") as infile:
        idx = 0
        for offset in range(0, filesize - (filesize % chunksize), chunksize):
            infile.seek(offset)
            with open(os.path.join(dirname, "{0}{1}.raw".format(filename, str(offset / chunksize).zfill(5))), "wb") as outfile:
                outfile.write(infile.read(chunksize))
            idx += 1
        if filesize % chunksize != 0:
            offset = filesize - (filesize % chunksize)
            infile.seek(offset)
            with open(os.path.join(dirname, "{0}{1}.raw".format(filename, str(offset / chunksize).zfill(5))), "wb") as outfile:
                outfile.write(infile.read(filesize % chunksize))
    """
    
            



if __name__ == "__main__":
    if len(sys.argv) < 6:
        print "Usage: python chunkify_mp4.py video-name output-dir frames-per-chunk width height bytes-per-pixel"
        sys.exit(1)
 
    main(*sys.argv[1:])

