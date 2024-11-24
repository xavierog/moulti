#!/usr/bin/env bash
MAX="$1"
function run {
	((STEP >= MAX)) && exit 0
	"$@"
	((++STEP))
}
run moulti set --title='This is MY (first) Moulti instance'
run moulti step add my_step --title='My first step'
# The documentation pipes the output of `ip -c a` but this is clearly not reproducible:
run moulti pass my_step <<EOF
1: [1;36mlo: [0m<LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback [1;33m00:00:00:00:00:00[0m brd [1;33m00:00:00:00:00:00[0m
    inet [1;35m127.0.0.1[0m/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 [1;34m::1[0m/128 scope host noprefixroute
       valid_lft forever preferred_lft forever
2: [1;36menxabcdef012345: [0m<BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state [1;32mUP [0mgroup default qlen 1000
    link/ether [1;33mab:cd:ef:01:23:45[0m brd [1;33mff:ff:ff:ff:ff:ff[0m
    inet [1;35m1.2.3.4[0m/24 brd [1;35m1.2.3.255 [0mscope global dynamic noprefixroute enxf44dad02f4c5
       valid_lft 78769sec preferred_lft 78769sec
    inet6 [1;34m2001:abc:def0:1234:5678:9abc:def0:1234[0m/64 scope global dynamic noprefixroute
       valid_lft 86400sec preferred_lft 14400sec
    inet6 [1;34mfe80::abc:def0:1234:4678[0m/64 scope link noprefixroute
       valid_lft forever preferred_lft forever
3: [1;36mwlp2s0: [0m<NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state [1;31mDOWN [0mgroup default qlen 1000
    link/ether [1;33m12:34:56:ab:cd:ef[0m brd [1;33mff:ff:ff:ff:ff:ff[0m permaddr [1;33mfe:dc:ba:65:43:21[0m
    altname wlxfedcba654321
EOF
run moulti step update my_step --classes='success'
run moulti step update my_step --top-text='Here is the output of [red bold]ip -color address[/]:'
run moulti step update my_step --bottom-text='[blink]blink[/] [bold]bold[/] [conceal]conceal[/] [italic]italic[/] [overline]overline[/] [reverse]reverse[/] [strike]strike[/] [underline]underline[/] [underline2]underline2[/] [blue]blue[/] [on yellow1]on yellow1[/] [blue on yellow1]blue on yellow1[/]'
for class in warning error inactive standard; do
    run moulti step add "${class}_example" \
        --classes="${class}" \
        --title="$(tr '[:lower:]' '[:upper:]' <<< ${class:0:1})${class:1} step" \
        --text="This is a step with class '${class}'." \
        --bottom-text=' '
done
run moulti step clear warning_example
run moulti step delete error_example
