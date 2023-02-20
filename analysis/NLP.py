from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
import re
from operator import itemgetter

def clean_text(post):
	temp = post.lower()
	temp = re.sub("'", "", temp) # to avoid removing contractions in english
	temp = re.sub("@[A-Za-z0-9_]+","", temp)
	temp = re.sub("#[A-Za-z0-9_]+","", temp)
	temp = re.sub(r'http\S+', '', temp)
	temp = re.sub('[()!?]', ' ', temp)
	temp = re.sub('\[.*?\]',' ', temp)
	temp = re.sub("[^a-z0-9]"," ", temp)
	temp = temp.split()
	stopwords = ["for", "on", "an", "a", "of", "and", "in", "the", "to", "from"]
	temp = [w for w in temp if not w in stopwords]
	temp = " ".join(word for word in temp)
	return temp

def get_score(post):
	post = clean_text(post)
	roberta = "cardiffnlp/twitter-roberta-base-sentiment-latest"
	tokenizer = AutoTokenizer.from_pretrained(roberta)
	model = AutoModelForSequenceClassification.from_pretrained(roberta)
	encoded_tweet = tokenizer(post, return_tensors='pt')
	output = model(**encoded_tweet)
	scores = (output[0][0].detach().numpy())
	scores = softmax(scores)
	
	return max([(i,item) for i, item in enumerate(scores)], key=itemgetter(1))[0]
  