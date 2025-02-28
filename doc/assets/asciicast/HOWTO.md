# demo-debian-upgrade.cast

Do not forget to unset MOULTI_CUSTOM_CSS

asciinema rec --title='Moulti demo: Debian upgrade' --cols=128 --rows=42 -c 'podman run -it moulti-demo' demo-debian-upgrade.cast

1. Click "Yes, upgrade"
2. Click "apt full-upgrade -y" to expand it:
2.1. Press Home
2.2. Grab the slider and scroll down to the bottom
3. Click "Collapse all"
4. Click "Expand all"
5. Grab the slider and scroll down to the bottom

asciinema rec --title='moulti_type demo' --cols=100 --rows=5 -c 'moulti run bash -c "moulti step add example --title=\ ; source moulti-functions.bash; moulti_type step update example --title This\ text\ appears\ one\ character\ at\ a\ time"' demo-moulti-type.cast
(but the resulting asciicast file was manually rewritten)
