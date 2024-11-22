#!/usr/bin/env bash

moulti buttonquestion add my_second_question \
	--title='My second question with Moulti' \
	--text='What is your name?' \
	--bottom-text='What a mess: https://en.wikipedia.org/wiki/Alice_and_Bob' \
	--button alice success Alice \
	--button bob primary Bob \
	--button craig default Craig \
	--button mallory error Mallory \
	--button oscar warning Oscar
answer=$(moulti buttonquestion get-answer my_second_question --wait)
[ "${answer}" ] && moulti step add answer --title='Got this answer' --text="${answer}"
