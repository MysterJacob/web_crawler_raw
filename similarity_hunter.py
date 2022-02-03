
import bs4
from difflib import SequenceMatcher
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

def seek(content : str,depth : int) -> list:
	
	parser = bs4.BeautifulSoup(content,'html.parser')
	layers = []
	html = parser.find("html")
	if html == None:
		return [content]

	layers.insert(0,[html])
	for i in range(depth):	
		for element in layers[0]:
			if type(element) is bs4.element.Tag:
				layers.insert(0,[x for x in list(element.children) if type(x) is bs4.element.Tag])
			
	
	layers.reverse()
	to_remove = ["href","src","content","nonce"]
	for layer in layers:	
		for element in layer:
			element.clear()
			for tr in to_remove:
				if tr in element.attrs:
					del element.attrs[tr]
	
	return [[y for y in x ] for x in layers]

def structureSimilarity(s1 : list,s2 : list):
	similarity = 0
	s1_len = len(s1)
	s2_len = len(s2)
	sequence_len = max(s1_len,s2_len)
	for i in range(sequence_len):
		s_s1 = str(s1[i]) if i < s1_len else ""
		s_s2 = str(s2[i]) if i < s2_len else ""
		weight = sequence_len - i + 1
		len_diff = abs(len(s_s2) - len(s_s1)) 
		weight *= len_diff + 1
		value = (1 - SequenceMatcher(None,s_s1,s_s2).ratio())
		
		similarity +=  value * weight
	return similarity

def calculatesSimilarity(content1 : str, content2 : str,depth : int) -> int:
	return structureSimilarity(seek(content1,depth),seek(content2,depth))

