
from CrawlerClass import Crawler
import argparse

def createParser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser()
	parser.add_argument('-t','--threads',metavar="Threads",type=int,default=1,help="Number of threads/workers")
	parser.add_argument('-l','--limit',metavar="Limit",type=int,default=0,help="Limit of crawled websites")
	parser.add_argument('-i','--interval',metavar="Interval",type=int,default=2000,help="Interval for searching, provided in miliseconds")
	default_user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36"
	parser.add_argument('-u','--user-agent',metavar="User agent",type=str,default=default_user_agent,help="User agent to send request")
	parser.add_argument('-r','--restore',dest="restore",action='store_true',help="Used to start from restore file.")

	parser.add_argument('url',metavar="url",type=str,help="Base url to start crawling")

	return parser

def createCrawler(args) -> Crawler:
	return Crawler(interval=args.interval,thread_count= args.threads,link_limit=args.limit)

def main():
	parser = createParser()
	args = parser.parse_args()
	crawler = createCrawler(args)

	if args.restore:
		crawler.startFormRestorefile(args.url)
	else:
		crawler.start(args.url)


if __name__ == "__main__":
	main()