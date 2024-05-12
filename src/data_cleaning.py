import re
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'\s+', ' ', text).strip()  # Remove extra whitespaces
    text = text.lower()  # Convert to lowercase
    return text

def preprocess_text(text):
    words = text.split()
    words = [word for word in words if word not in stopwords.words('english')]
    stemmer = PorterStemmer()
    words = [stemmer.stem(word) for word in words]
    return ' '.join(words)

def clean_tabular_data(data, fill_value=0):
    # Assume data is a list of dictionaries
    for row in data:
        for key, value in row.items():
            if value is None:
                row[key] = fill_value
    return data

