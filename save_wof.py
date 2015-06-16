import json
from string import capwords
import re

line_type = ""
hm_dict = {}


with open("wof_list.txt", "r") as read_file:
    for line in read_file:
        line = line.strip()
        if "-Category-" in line:
            line_type = "category"
            continue
        elif "-Phrases-" in line:
            line_type = "phrases"
            continue
        if line_type == "category":
            current_category = line
            hm_dict[line] = []
        elif line_type == "phrases":
            line_list = []
            for word in re.split(" ", line):
                if "." in word:
                    line_list.append(word.upper())
                else:
                    line_list.append(word.capitalize())
            hm_dict[current_category].append(" ".join(line_list))

with open("hm_phrase_dict.json", "w") as out_file:
    json.dump(hm_dict, out_file)
