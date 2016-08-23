#!/usr/bin/python3

# Stolen from /usr/share/doc/python3-dns/examples

# $ host -t SRV _librarian._tcp.fame1.l4tm.fc.us.rdlabs.hpecorp.net
# _librarian._tcp.fame1.l4tm.fc.us.rdlabs.hpecorp.net has SRV record 0 0 9093 torms.

from pdb import set_trace

import DNS

# automatically load nameserver(s) from /etc/resolv.conf
# (works on unix - on others, YMMV)

# DNS.ParseResolvConf()   # Rocky commented this out

set_trace()
r = DNS.Request(qtype='srv')
res = r.req('_librarian._tcp.fame1.l4tm.fc.us.rdlabs.hpecorp.net')

res.show()

print(res.answers)
