import queue
import logging
 
import betfairlightweight
from betfairlightweight import StreamListener
 
# setup logging
logging.basicConfig(level=logging.INFO)
 
# create trading instance (no need to put in correct details)
trading = betfairlightweight.APIClient('username', 'password')
 
# create queue for outputting market books
output_queue = queue.Queue()
 
# create listener
listener = StreamListener(
    output_queue=output_queue,
    max_latency=1e100
)
 
# create historical stream
stream = trading.historical.create_stream(
    directory='/Users/liampauling/Downloads/Sites 3/xdw/api/c0a022d4-3460-41f1-af12-a0b68b136898/BASIC-1.132153978',
    listener=listener
)
 
# start stream
stream.start(async=False)