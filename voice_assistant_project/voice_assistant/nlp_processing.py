import spacy
from spacy.matcher import PhraseMatcher
from spacy.lang.en.stop_words import STOP_WORDS

nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

custom_stop_words = ['is']
for word in custom_stop_words:
    STOP_WORDS.add(word)
    nlp.vocab[word].is_stop = True

def extract_keywords(text, recall_phrases):
    # If using all conversation, extracts keywords to search with for context
    stop_phrases_patterns = [nlp(phrase) for phrase in recall_phrases]
    matcher.add("StopPhrases", stop_phrases_patterns)

    doc = nlp(text)
    print(f"doc: {doc}")
    matches = matcher(doc)
    for match_id, start, end in matches:
        for token in doc[start:end]:
            token.set_extension("is_stop_phrase", default=False, force=True)
            token._.is_stop_phrase = True

    keywords = []

    for chunk in doc.noun_chunks:
        print(f"chunk: {chunk}")
        token = chunk.text.lower()
        if token not in STOP_WORDS and chunk.root.pos_ != "PRON" and chunk.root.pos_ != "AUX" and not any(tok._.is_stop_phrase for tok in chunk): #removes pronouns, aux verbs and stop_words
            if not keywords:
                for inner_token in doc:
                    if inner_token.pos_ == "NOUN" and not inner_token.is_stop and inner_token.text.lower() not in [phrase.lower() for phrase in recall_phrases]:
                        keywords.append(inner_token.text.lower())
            print(f"Adding keyword: {token}")
            keywords.append(token)

    # Remove duplicates and limit keywords
    unique_keywords = list(set(keywords))
    max_keywords = 5
    return unique_keywords[:max_keywords]

def search_conversation_history(conversation_history, keywords):
    #searches entire databse for those keywords
    results = []
    for entry in conversation_history:
        if any(str(keyword).lower() in entry[2].lower() for keyword in keywords) and entry not in results:
            results.append(entry)
    return results

def remove_duplicates(conversation_history):
    unique_history = []
    content_set = set()
    for entry in conversation_history:
        content = entry[2]
        if content not in content_set:
            unique_history.append(entry)
            content_set.add(content)
    return unique_history
