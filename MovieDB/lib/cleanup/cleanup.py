#!/usr/bin/env python3
import traceback
import os
import re
import time

CODE_PATH = "/home/pi/bin/cleanup"
PATH = "/home/pi/share/torrent-complete"
#PATH = "/home/pi/share/cleanup-test-dir"
print("PATH: {}\n".format(PATH))

def debug(lines):
    with open(os.path.join(CODE_PATH, "debug.txt"), "a") as file_out:
        for line in lines:
            file_out.write(line)

def split(path):
    terms = path.split(".")
    if len(terms) > 2:
        print("Split on period... " + str(terms))
        return terms

    terms = path.split(" ")
    if len(terms) > 0:
        print("Split on space... " + str(terms))
        return terms

    print("No split... " + str([path]))
    return [path]

def get_year(terms):
    possible = []
    PATTERN = "(\d{4})"

    for term in terms:
        match = re.search(PATTERN, term)
        if match:
            possible.append(match.group(1))

    for number in possible:
        if int(number) > 1920 and int(number) < 2030:
            return number

    return "NULL"

partial_spam = []
specific_spam = []
def load_spam():
    with open(os.path.join(CODE_PATH, "spam.txt"), "r") as file_in:
        spam = file_in.read().splitlines()

    partial = False
    for line in spam:
        if not re.search("^[\s\[]", line):
            if partial:
                partial_spam.append(line)
            else:
                specific_spam.append(line)
        if line == "[ PARTIAL ]":
            partial = True

def remove_spam(terms):
    if len(terms) <= 1:
        print("remove_spam() was given 1-term title, returning... " + str(terms))
        return terms 

    clean_terms = []

    for term in terms:
        clean = True
        if term.lower() in specific_spam:
            print("specific: " + term)
            clean = False
        else:
            for spam in partial_spam:
                if re.search(spam, term, re.IGNORECASE):
                    print("partial: " + term)
                    clean = False

        if clean:
            print("Clean: " + term)
            clean_terms.append(term)

    if len(clean_terms) < 1:
        print("remove_spam() wants to return empty [], returning... " + str(terms))
        return terms

    return clean_terms
        

def cleanup(path_info):
    new_path = ""
    extension = ""

    path = path_info[0]
    file = path_info[1]

    try:
        if file != "FOLDER":
            extension = file.split(".")[-1]
            print("OG File: " + file)
            terms = split(file)
            print("Terms returned after split(): " + str(terms))
            for index, term in enumerate(terms):
                terms[index] = re.sub("\.*"+extension, "", term)
            print("Terms[:-1]: " + str(terms))
            year = get_year(terms)
            for index, term in enumerate(terms):
                terms[index] = re.sub("\(*"+year+"\)*", "", term)
            terms = remove_spam(terms)
            if len(terms) == 1:
                title = terms[0]
            else:
                title = " ".join(terms).strip()
            new_path = os.path.join(path, "({}) {}.{}".format(year, title, extension))
            og_path = os.path.join(path_info[0], path_info[1])
            print(og_path)
            print(new_path)
            print("")
            os.rename(og_path, new_path)
        else:
            file = path.split("/")[-1]
            print(file)
            path = path.replace(file, "") 
            terms = split(file)
            year = get_year(terms)
            for term in terms:
                if re.search(year, term):
                    terms.remove(term)
            print(terms)
            terms = remove_spam(terms)
            if len(terms) == 1:
                title = terms[0]
            else:
                title = " ".join(terms).strip()
            new_path = os.path.join(path, "({}) {}".format(year, title))
            og_path = path_info[0]
            print(og_path)
            print(new_path)
            print("")
            os.rename(og_path, new_path)
    except Exception as e:
        print("Error: " + traceback.format_exc())
        debug(["Error: " + traceback.format_exc(), "  OG Path: " + path_info[0], "  OG File: " + path_info[1]])
        debug(["  Path: " + path, "  File: " + file])


def get_paths(startpath):
    paths = []
    for root, dirs, files in os.walk(startpath):
        for dir in dirs:
            paths.append([os.path.join(root, dir), "FOLDER"])
        for file in files:
            paths.append([root, file])
    return paths

def main():
    return
    time.sleep(120)
    load_spam()
    paths = get_paths(PATH)
    for path in paths[::-1]:
        cleanup(path)

if __name__ == '__main__':
    main()
