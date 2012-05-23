from states.base import StateBase
from deploy.conf import settings




from pipeline.feedripper import do_viacsv

class State(StateBase):
	ripper = do_viacsv()
	def _get_feed_path(self):
		return 'data/vip_feeds/vipFeed-39-2012-03-06.xml'