#!/usr/bin/env bash

empty_file="/tmp/empty-$$"
> "${empty_file}"

moulti step add pipe_empty_file --title="cat empty_file | moulti pass"
cat "${empty_file}" | moulti pass pipe_empty_file

moulti step add pipe_dev_null --title="cat /dev/null | moulti pass"
cat /dev/null | moulti pass pipe_dev_null

moulti step add empty_file --title="moulti pass < empty_file"
moulti pass empty_file < "${empty_file}"

moulti step add empty_dev_null --title="moulti pass < /dev/null"
moulti pass empty_dev_null < /dev/null

rm "${empty_file}"
