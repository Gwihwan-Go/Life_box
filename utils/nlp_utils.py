#This file deals with the language data
# Categorizing Logic
# raw_words -> core_words -> lemmatization -> if any word of words in category_list -> category

import json
import re
keylist_save_path = "resources/key_list.json"
unlist_words_path = 'resources/unlisted_words.txt'
def load(save_path) :
    """
    load key_list from save_path
    input :
        save_path(str) : saved path
    output :
        results(dict) : key_list
    """
    with open(save_path) as d:
        results = json.load(d)
    d.close()
    return results

def search(target,key_list) :
    """
    search target word from key_list
    key_list is looks like {key : [word1, word2, ...], key2 : [ ...]}
    input :
        target(str) : word to change ex) nap, lunch
        key_list(dict) : looks like {key : [word1, word2, ...], key2 : [ ...]}
    output :
        result(str) : changed word ex) 🌙sleep, 🍔food
        None : if target isn't exist in key_list
    """
    target = target.lower()
    for key, word_list in key_list.items() :
        if target in word_list :
            return key

    return None


## add new key
def add(key, value, key_list) :
    """
    add {key:value} to dic
    key_list is looks like {key : [word1, word2, ...], key2 : [ ...]}
    input :
        key(str) : changed word ex) 🌙sleep, 🍔food
        value(str) : word to change ex) nap, lunch
        key_list(dict) : looks like {key : [word1, word2, ...], key2 : [ ...]}
    output :
        -1(int) : if the value already existed in key list, return -1
        key_list(dict) : updated key_list
    """
    if search(value,key_list) != value :
        print("The value already existed in key_list, no update has proceeded")
        return key_list
    if key in [key[1:] for key in key_list.keys()] :
        key_list[key].append(value)
    else :
        key_list[key]=[value]
    
    return key_list

def save(key_list, save_path) :
    """
    save key_list to save_path
    input :
        key_list(dict) : looks like {key : [word1, word2, ...], key2 : [ ...]}
        save_path(str) : path to save at
    """
    import json
    json = json.dumps(key_list)

    # open file for writing, "w" 
    f = open(save_path,"w")

    # write json object to file
    f.write(json)

    # close file
    f.close()
    print(f"file has successfuly saved at {save_path}")

def preprocess(word) :
    """
    algorithm of preprocessing words into core meaningful word

    correct spelling of words

    input :
        words(str) : target word
    output :
        words(list) : list of words
    """
    ###############
    ##############
    #####NEED######
    ##############
    ############
    return correct_word(word) #correct spelling of words
def correct_word(words) :
    """
    algorithm of preprocessing words into core meaningful word

    correct spelling and lemmatizing words

    input :
        word(str) : target word, or words
    output :
        words(str) : corrected word
    """
    from textblob import TextBlob
    from textblob import Word

    if len(words) > 0 :
        for word in words.split() :
            # if corrected is not alphabet word 
            corrected = TextBlob(word).correct()
            if len(corrected) > 0 :
                try :
                    new_word = Word(corrected).lemmatize(corrected.tags[0][1]) #lemmatize
                    words = words.replace(word, str(new_word))
                except :
                    print('no tags', corrected)
    else : #if word is empty
        words = 'others'
    return words

def print_and_clear_unlist_words() :
    """
    print unlisted words and delete file
    """
    # clear unlisted_words.txt file
    f = open(unlist_words_path, 'r')
    for word in f.read().strip().split('\n') :
        print(f"unlisted words : {word}")
    f.close()

    f = open(unlist_words_path, 'w')
    print("unlisted words file has been cleared")
    f.close()

def get_unlist_words(words) :
    """
    get unlisted words

    input :
        words(str) : target words
    """
    # if text file exists, append
    # else, create new file
    f = open(unlist_words_path, 'a')
    f.write(f"{words}\n")
    f.close()

def categorize(words) :
    """
    algorithm of categorizing words
    input :
        word(str) : target word or words ex) 'nap', 'play at park'
    output :
        category(str) : representation of the word
    """
    key_list=load(keylist_save_path)
    words = re.sub('[^a-zA-Z]+', ' ', words) #remove non-alphabet from
    for word in words.split() :
        word = preprocess(word)
        cate = search(word, key_list) ##categroize dictionary key to more representative ones
        if cate is not None :
            print(f"{cate} <- {words}({word})", end='') # continue print divided hour at interpret_table_contents in html_parser 
            return cate
    get_unlist_words(preprocess(words))
    print(f"{preprocess(words)}({words}) doesn't exist in the key list", end='')
    return 'others'

if __name__ == "__main__" :
    # print(categorize(['coda - homwork (hi) hello']))
    print_and_clear_unlist_words()
