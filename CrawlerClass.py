from base64 import b64decode,b64encode
import requests
import time
from threading import Thread
import re
from similarity_hunter import calculatesSimilarity

SIMILARITY_DEPTH = 5
SIMILARITY_THRESHOLD = 50


class Crawler():
	def __init__(self,interval=2000,restorefile="./crawler.restore",thread_count=1,link_limit=0,domain="",user_client="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36") -> None:

		self.interval = interval
		self.thread_count = thread_count
		self.link_limit = link_limit
		self.domain_limit = domain
		self.user_client = user_client
		
		self.restorefile = None
		if not restorefile == "":
			self.restorefile = open(restorefile,"r+")


		self.link_queue = []
		self.all_enqueued_links = []
		self.workers = []

	def __del__(self):
		if not self.restorefile == None:
			self.restorefile.close()

	def parseLink(self,url : str) -> tuple:
		mask = r'^(http[s]?)?(?::\/\/)?((?:[A-z0-9\-\%]+\.{0,1})*)(?::)?([0-9]*)?((?:\/[A-z0-9\-\%]*)*(?:\.[A-z0-9\-\%]*)?)?((?:[?&][A-z0-9\-\%]*=[A-z0-9\-\%]*)*)?'
		matched = re.match(mask,url)
		if matched == None:
			return "","","",""
		groups = matched.groups()
		# Protocol, domain, port, path, args
		return groups[0],groups[1],groups[2],groups[3],groups[4]

	def encodeToBase64(self,url : str):
		return str(b64encode(url.encode("ASCII")))[2:-1]

	def decodeFromBase64(self,enc : str):
		return str(b64decode(enc))[2:-1]

	def readRestorefile(self) -> tuple:
		if not self.restorefile == None:
			queue = self.restorefile.readline()
			queue = [self.decodeFromBase64(u) for u in queue.split(",")]
			all_enqueued_links = self.restorefile.readline()
			all_enqueued_links = [self.decodeFromBase64(u) for u in all_enqueued_links.split(",")]
			return queue,all_enqueued_links
		return ([],[])

	def updateRestorefile(self):
		if not self.restorefile == None:
			self.restorefile.seek(0)
			self.restorefile.write(",".join([self.encodeToBase64(u) for u in self.link_queue]))
			self.restorefile.write("\n")
			self.restorefile.write(",".join([self.encodeToBase64(u) for u in self.all_enqueued_links]))

	def enqueueLink(self,url : str) -> None:
		protocol,domain,port,path,args = self.parseLink(url)
		if not args == "" and not args == None:
			new_url = re.sub(r'((?:[?&][A-z0-9\-\%]*=[A-z0-9\-\%]*)*)?',"",url)
			self.enqueueLink(new_url)

		if not url in self.all_enqueued_links and not url == "" and\
		not protocol == "" and\
		(self.link_limit == 0 or not len(self.all_enqueued_links) > self.link_limit) and\
		(self.domain_limit == "" or self.domain_limit == domain):

			self.link_queue.insert(0,url)
			self.all_enqueued_links.append(url)

		self.updateRestorefile()

	def popLink(self) -> str:
		if len(self.link_queue) == 0:
			return ""
		url = self.link_queue.pop() 
		self.updateRestorefile()
		return url

	def start(self,url : str):
		self.enqueueLink(url)
		for _ in range(self.thread_count):
			worker = CrawlerWorker(self)
			self.workers.append(worker)
		
		for worker in self.workers:
			time.sleep(0.2)
			worker.start()

	def startFormRestorefile(self, url : str):
		self.link_queue,self.all_enqueued_links = self.readRestorefile()
		#print(self.readRestorefile())
		self.start(url)

class CrawlerWorker(Thread):
	def __init__(self,crawler : Crawler):
		super().__init__()
		self.crawler = crawler
		self.queue = crawler.link_queue

	def run(self) -> None:
		while not len(self.queue) == 0:
			url = self.crawler.popLink()
			self.crawl(url)
			time.sleep(self.crawler.interval/1000)

	def parseContent(self,response : requests.Response):
		content = response.content
		text = response.text
		pattern = r'(?<!\<)(?:(?:http[s]?\:\/\/)|(?:\/))(?:[A-z0-9\-\%]+\.{0,1})+(?:[A-z0-9\-\%\/\&\=\?\.])*';
		urls = re.findall(pattern,text)
		print(response.url, ":" ,urls)
		base_protocol,base_domain,_,_,_ = self.crawler.parseLink(response.url)
		for url in urls:
			if url.startswith("/"):
				base = base_protocol + "://" + base_domain
				url = base + url
			corrected_url = re.sub(r'(127\.0\.0\.[0-9]{1,3}|localhost)',base_domain,url)
			_,_,_,path,_ = self.crawler.parseLink(corrected_url)
			
			
			if len(path) <= 4:
				self.crawler.enqueueLink(corrected_url)
			else:
				self.enqueueLink(content,corrected_url)

	# Temporary name, need for refactorization
	def enqueueLink(self,parent_content : str ,url : str):
		time.sleep(1)
		try:
			response = self.request(url)
		except:
			return
		simiarity = calculatesSimilarity(parent_content,response.content,SIMILARITY_DEPTH)
		if not simiarity < SIMILARITY_THRESHOLD:
			self.crawler.enqueueLink(url)




	def request(self, url : str) -> requests.Response:
		userclient = self.crawler.user_client
		headers = {
			'User-Agent': userclient,
			'From': 'aeaeaeae.tv'
		}
		return requests.get(url,headers=headers,allow_redirects=True,timeout=30)

	def crawl(self,url : str) -> None:
		protocol,domain,port,path,args = self.crawler.parseLink(url)

		if protocol == "":
			return

		try:
			response = self.request(url)
		except Exception as err:
			print("Failed on {} - [{}]".format(url,err.args[0]))
			return
			
		if response.ok:
			self.parseContent(response)
