#!/bin/bash

SCRIPTDIR=$(dirname "$0")

[ -d "$SCRIPTDIR/../data" ] || mkdir "$SCRIPTDIR/../data"

# Install Contract Understanding Atticus Dataset (CUAD v1)
curl -L https://zenodo.org/records/4595826/files/CUAD_v1.zip\?download\=1 -o $SCRIPTDIR/CUAD_v1.zip && \
    unzip $SCRIPTDIR/CUAD_v1.zip -d $SCRIPTDIR/../data && \
    rm $SCRIPTDIR/CUAD_v1.zip

# Install the SBD Adjudicatory Decisions Dataset
git clone git@github.com:jsavelka/sbd_adjudicatory_dec.git $SCRIPTDIR/../data/sbd_adjudicatory_dec
