#!/bin/bash

# lambda deps
if [[ ! -d /tmp/root ]]; then
    pushd .
    cd /tmp
    curl https://s3.amazonaws.com/jemmons-test/root-495M-2017-02-06.tar.gz | tar xz
    popd
fi

if [[ ! -d root ]]; then
    ln -s /tmp/root .
fi

if [[ ! -f env.sh ]]; then
    ln -s root/env.sh .
fi

# lfw
if [[ ! -d lfw_funneled ]]; then
    curl https://s3.amazonaws.com/jemmons-test/lfw-funneled.tgz | tar xz
fi

# precomputed lfw features
if [[ ! -f ../models/lfw_face_vectors.csv.gz ]]; then
    curl  https://s3.amazonaws.com/jemmons-test/lfw_face_vectors.csv.gz > ../models/lfw_face_vectors.csv.gz
fi
