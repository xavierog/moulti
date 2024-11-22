#!/usr/bin/env bash

moulti step add 1
moulti pass 1 <<EOF
line1
line2
line3
EOF

moulti step add 2 --text=$'line1\nline2\nline3'

moulti step add 3
moulti step update 3 --text=$'line1\nline2\nline3'

moulti step add 4
moulti step clear 4
moulti step append 4 'line1' 'line2' 'line3'
