#!/usr/bin/env bash

moulti question add my_third_question \
    --title='My third question with Moulti' \
    --text='What is your name?' \
    --bottom-text='I live on the second floor' \
    --placeholder='Enter your name in this input field, or click a button' \
    --button 'My name is Alice' default Alice \
    --button 'My name is Bob' default Bob \
    --button 'My name is {input}' success 'Neither, use input'
answer=$(moulti question get-answer my_third_question --wait)
moulti step add answer --title='Got this answer' --text="${answer}"
