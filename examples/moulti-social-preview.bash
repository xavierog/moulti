#!/usr/bin/env bash
export MOULTI_INSTANCE='social-preview'
[ "${MOULTI_RUN}" ] || exec moulti run "$0" "$@"
moulti wait
moulti step add title --title='This is a Moulti [italic]step[/]' --top-text='It was made using [yellow1 bold]moulti step add[/] and shall display MOULTI:' --bottom-text='Neat, eh? I made it with [yellow1 bold]toilet -f mono12 --metal[/]'
toilet -w 130 -f mono12 --metal '    MOULTI' | head -8 | tail -n +2 | moulti pass title
moulti step add step_ping --classes='success' --title="PING example.org ($(dig +short AAAA example.org)) 56 data bytes" --max-height=5 --min-height=5 --bottom-text='This is a second step, made via [blue1 bold]ping example.org | moulti pass step_ping[/]'
ping example.org | moulti pass step_ping &
moulti step add collapsed --classes='warning' --title='This step probably shows things of the utmost importance, but right now it is collapsed.' --collapse --text='Gotcha! There is nothing in here!'
moulti step add script    --classes='error'   --title='Anyway, here is the script that generated all of this:'
batcat -f -n -l bash "$0" | moulti pass script
