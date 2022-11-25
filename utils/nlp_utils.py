#This file deals with the language data
# Categorizing Logic
# raw_words -> core_words -> lemmatization -> if any word of words in category_list -> category

import json
import re
keylist_save_path = "resources/key_list.json"

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
    result = target
    for key, word_list in key_list.items() :
        #if any words in sentence in word_list 
        # print(word_list)
        # any word in target is in word_list 
        for word in target.split() :
            if word in word_list :
                result = key
                return result

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

def preprocess(words) :
    """
    algorithm of preprocessing words into core meaningful word
    if words includes '/' -> split it and give list

    correct spelling of words

    input :
        words(str) : target words, may include '/'
    output :
        words(list) : list of words
    """
    split_symbol = '/' 
    ###############
    ##############
    #####NEED######
    ##############
    ############
    return [correct_word(word) \
            for word in words.split(split_symbol)] #correct spelling of words
def correct_word(words) :
    """
    algorithm of preprocessing words into core meaningful word
    if words includes '/' -> split it and give list

    correct spelling and lemmatizing words

    input :
        words(str) : target words
    output :
        words(str) : corrected word
    """
    from textblob import TextBlob
    from textblob import Word

    print('before',words)

    if len(words) > 0 :
        for word in words.split() :
            corrected = TextBlob(word).correct() #correct spelling of words
            # if corrected is not alphabet word 
            if re.match("^[a-zA-Z]*$", str(corrected)) :
                new_word = Word(corrected).lemmatize(corrected.tags[0][1]) #lemmatize
                words = words.replace(word, str(new_word))

    else : #if word is empty
        words = 'others'
    print('after',words)
    return words
    
def categorize(words) :
    """
    algorithm of categorizing words
    input :
        word(str) : target word
    output :
        category(str) : representation of the word
    """
    key_list=load(keylist_save_path)
    words = preprocess(words)
    for idx in range(len(words)) :
        
        cate = search(words[idx], key_list) ##categroize dictionary key to more representative ones
        if cate is not None :
            words[idx]=cate
        else :
            print(f"element : {words[idx]} doesn't exist in the key list")
            words[idx] = 'others'
    return words

if __name__ == "__main__" :
    print(categorize('coda - hi hello'))

