#!/usr/bin/env bash

moulti inputquestion add my_first_question \
    --title='My first question with Moulti' \
    --text='What is your name?' \
    --bottom-text='We want information... information... information!' \
    --placeholder='Please enter your name in this input field'
answer=$(moulti inputquestion get-answer my_first_question --wait)
moulti step add answer --title='Got this answer' --text="${answer}"
