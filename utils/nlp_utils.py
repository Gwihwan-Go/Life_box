#This file deals with the language data

import json

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
        if target in word_list :
            result = key
            break
    if result != target :  
        return result   
    else :
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
def correct_word(word) :
    """
    algorithm of preprocessing words into core meaningful word
    if words includes '/' -> split it and give list

    correct spelling of words

    input :
        word(str) : target words
    output :
        word(str) : corrected word
    """
    from textblob import TextBlob

    if len(word) > 0 :
        word = TextBlob(word).correct()
    else : #if word is empty
        word = 'others'

    return word
    
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
    print(categorize('stdy/naap/lanch'))