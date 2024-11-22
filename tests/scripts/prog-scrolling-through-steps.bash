#!/usr/bin/env bash

# Create 5 steps:
echo {1..4} | xargs -n 1 moulti step add
moulti step add 5 --bottom-text='This is the very last line of step 5'

# Fill them with lorem ipsum text:
((++i))
nl -ba <<EOF | moulti pass $i
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus ut odio
nisl. Sed sit amet tempus ipsum. Pellentesque tincidunt, massa et finibus
condimentum, nulla justo eleifend purus, vel dapibus leo arcu eu sem. Nulla
sagittis augue lobortis lorem lacinia facilisis. Morbi volutpat venenatis ante.
Vivamus erat leo, molestie at vehicula vel, varius tincidunt tortor. Vivamus ac
enim nulla. Sed nunc enim, malesuada id felis vel, consectetur semper arcu.
EOF

((++i))
nl -ba <<EOF | moulti pass $i
Donec vel neque fringilla, tincidunt magna et, volutpat tellus. Curabitur sit
amet arcu eget enim sagittis malesuada. Fusce fermentum, diam vitae
pellentesque pretium, urna enim tempus neque, a vehicula est nisi ut lorem.
Cras aliquet tortor eget massa ultricies, nec maximus tellus interdum. In eget
erat non dolor pulvinar lacinia. Proin maximus posuere tortor at cursus. Etiam
volutpat diam libero, non convallis elit gravida eu. Maecenas fringilla nisi eu
mi iaculis, ultrices posuere erat pulvinar. Pellentesque feugiat viverra ex nec
placerat. Curabitur id dolor congue, malesuada justo dictum, tincidunt augue.
Vivamus dapibus lacus ac fringilla tempor. Suspendisse potenti. Quisque orci
nisi, interdum eu felis sit amet, ultricies vulputate nulla. Duis at justo
hendrerit ipsum vulputate posuere ac a est. Donec iaculis nisi id rhoncus
convallis.
EOF

((++i))
nl -ba <<EOF | moulti pass $i
Phasellus venenatis id augue auctor bibendum. Suspendisse vitae libero sit amet
justo commodo gravida vel vitae arcu. Mauris nisl purus, dapibus aliquam
fringilla mollis, mollis vel dolor. Donec lorem justo, dignissim ac egestas
non, fringilla ac massa. Sed nec rhoncus tellus, sit amet semper purus.
Phasellus venenatis egestas justo vel dapibus. Donec bibendum, tellus ac
aliquam mattis, tortor elit blandit lorem, at ultricies diam diam at velit.
Phasellus congue purus erat, ut scelerisque felis dignissim at.
EOF

((++i))
nl -ba -v -7 <<EOF | moulti pass $i
Integer dictum urna magna, quis tempor elit varius eget. Pellentesque mattis
pharetra maximus. Aliquam mollis ipsum in eros tempor, a feugiat lorem
porttitor. Donec vel pretium ante. Nam eu lorem suscipit, tristique leo non,
pulvinar elit. Aliquam metus erat, euismod vel nisl nec, mollis fringilla nisl.
Maecenas sit amet varius mauris, in accumsan risus. Pellentesque interdum
porttitor nulla vel bibendum. Nullam porta lectus in dui rutrum, sed mollis dui
mollis. Nullam quam sapien, faucibus nec lacus et, efficitur pharetra odio.
EOF

((++i))
nl -ba <<EOF | moulti pass $i
Fusce a nibh ac massa ullamcorper condimentum. Nam euismod pulvinar tellus id
euismod. Mauris condimentum, odio sit amet faucibus ornare, magna turpis cursus
mi, laoreet pulvinar ex purus a nunc. Aenean non lectus id urna euismod
efficitur. Etiam at faucibus arcu. Phasellus lorem eros, ullamcorper sed
dignissim id, pellentesque ac felis. Mauris sit amet risus in quam finibus
egestas. Phasellus blandit eros ut tempor aliquam. Nulla aliquet odio laoreet
lorem sollicitudin tincidunt. Aliquam aliquet dignissim libero quis sodales.
Sed eleifend nulla vitae diam gravida, aliquet tempus ante rhoncus. In at
facilisis diam. In sollicitudin libero dolor, fringilla sagittis ex dignissim
vel. Nullam ex libero, posuere nec massa vel, mollis facilisis dolor. Phasellus
congue nibh arcu. Donec vestibulum pellentesque eros.
EOF

case "$1" in
	# moulti scroll
	1) moulti scroll 5;;
	2) moulti scroll 4 -3;;
	3) moulti scroll 5 3;;
	# Scroll on activity
	4)
		# By default, steps do not scroll on activity:
		moulti pass --append 5 <<< 'do not scroll!'
		;;
	5)
		# Enable scroll on activity:
		moulti step update 5 --scroll-on-activity=true
		moulti pass 5 --append <<< 'scroll!'
		;;
	6)
		# A typical use case is to ensure the last line of output is displayed:
		moulti step update 5 --max-height=0 --scroll-on-activity=-2
		yes 'scroll to the last line!' | nl -ba | head -500 | moulti pass 5 --append
		;;
	7)
		# Enable then disable scroll on activity:
		moulti step update 5 --scroll-on-activity=true
		moulti step update 5 --scroll-on-activity=false
		moulti pass 5 --append <<< 'do not scroll!'
		;;
esac
