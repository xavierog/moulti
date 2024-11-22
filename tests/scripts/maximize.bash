#!/usr/bin/env bash

# Create 5 steps:
xargs -n 1 moulti step add --min-height=5 --max-height=5 <<< 'one two three four five'
moulti step update five --max-height=0
yes 'content' | head -5   | nl -ba | moulti pass one
yes 'content' | head -10  | nl -ba | moulti pass two
yes 'content' | head -15  | nl -ba | moulti pass three
yes 'content' | head -20  | nl -ba | moulti pass four
yes 'content' | head -100 | nl -ba | moulti pass five
