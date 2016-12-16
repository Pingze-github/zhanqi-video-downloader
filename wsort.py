# coding=u8

import re

re_digits = re.compile(r'(\d+)')  
  
def emb_numbers(s):  
    pieces=re_digits.split(s)  
    pieces[1::2]=map(int,pieces[1::2])
    return pieces  

def wsort(alist):  
    return sorted(alist, key=emb_numbers) 

def wsort2(alist):  
    aux = [(emb_numbers(s),s) for s in alist]  
    aux.sort()  
    return [s for __,s in aux]  
