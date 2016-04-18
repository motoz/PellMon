class protocol_error(Exception):
    pass
class seqnum_error(protocol_error):
    pass
class protocol_timeout(protocol_error):
    pass
class protocol_offline(protocol_error):
    pass
