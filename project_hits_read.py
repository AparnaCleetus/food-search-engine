# -*- coding: utf-8 -*-
"""
Created on Sun Apr 26 12:53:48 2020

@author: aparn
"""
from urllib.request import urlopen
import io
import networkx as nx
import re
import json
import sys
import os
import simplejson
import matplotlib.pyplot as plt

url_title = {}
url_list = []
G = nx.Graph()
root_dic = {}
base_dic = {}
results_dic = {}
query_string = ""


def content_process(content):
    content_list = []
    content = content.replace('\\', '')
    content = content.replace('[', '')
    content = content.replace(']', '')
    content = content.replace('\'', '')
    content = content.replace('\"', '')
    content = content.replace("\n", ' ')
    content = content.replace("\r", " ")
    str_loc = str(content).find(query_string)
    if str_loc != -1:
        if str_loc - 150 > 0:
            content = content[str_loc - 150:str_loc + 150]
        else:
            content = content[0:str_loc + 150]
        content_list = content.split(" ")
        content = ' '.join(content_list[1:len(content_list) - 2])
    return content


def read_json(data_file):
    data_file = data_file.replace(" ", "%20")
    print(data_file)
    if os.path.exists(data_file + ".txt"):
        f = open(data_file + ".txt", encoding="utf-8")
        data = json.load(f, strict=False)
    else:
        connection = urlopen(
            'http://localhost:8983/solr/nutch/select?fl=*%2C%20score&q=content:\"' + data_file + '\"&rows=' + str(
                70) + '&sort=score%20desc&start=' + str(0) + '&wt=json')

        data = simplejson.load(connection)
        print("solr output", data)
        with open(data_file + ".txt", 'w') as output_file:
            json.dump(data, output_file)

    query_string = str(data["responseHeader"]["params"]["q"].split(":")[1])
    query_string = query_string.replace('\'', '')
    query_string = query_string.replace('\"', '')

    for i in data["response"]["docs"]:
        url = str(i["url"])
        if "nutch.apache.org" in url:
            continue
        url = url.replace('\'', '')
        url = url.replace('\"', '')
        url = url.replace('[', '')
        url = url.replace(']', '')
        if "title" in i:
            title = str(i["title"])
            title = title.replace('[', '')
            title = title.replace(']', '')
            title = title.replace('\'', '')
            title = title.replace('\"', '')
            title = title.replace('|', '')
        else:
            title = url
        if "content" in i:
            content = str(i["content"])
            content = content_process(content)
        else:
            content = url
        url_list.append(url)
        url_title[url] = [title, content]
    # print(url_title)


def read_crawl_list(arg2):
    with io.open(arg2, 'r', encoding="utf-8") as file_url:
        lines = file_url.readlines()
        for line in lines:
            if line.find("http") == 0:
                root = line.split('\t')[0]
                link = []
            elif " fromUrl" in line:
                line = re.sub(r'[\n]', r'', line)
                link.append(line.split(" ")[2])
            else:
                root_dic[root] = link
                continue
    # print(root_dic)


def build_adj_list():
    new_list = []
    for query_line in url_list:
        if query_line in root_dic:
            base_dic[query_line] = root_dic[query_line]
        else:
            for root_list in root_dic:
                for list_root in root_dic[root_list]:
                    # print(list_root+":"+query_line)
                    if list_root == query_line:
                        # print(list_root+":"+query_line)
                        if query_line in base_dic:
                            base_dic[query_line].append(root_list)
                        else:
                            new_list.append(root_list)
                            base_dic[query_line] = new_list
            new_list = []
    # print(base_dic)


def build_graph():
    for base_line in base_dic:
        for link in base_dic[base_line]:
            G.add_edge(base_line, link)
    # plt.figure(figsize =(10, 10))
    # nx.draw_networkx(G, with_labels = True)


def calc_hits():
    return nx.hits(G, max_iter=2000, normalized=True)
    # print("Hub Scores: ", hubs)


# print("Authority Scores: ", authorities)


def build_results_dict(hubs, authorities):
    j = 1
    url = {}
    content = {}
    title = {}
    res_url = []
    results_list = []
    for link, score in authorities.items():
        results_list.append(link)
    for link, score in hubs.items():
        if link in results_list:
            continue
        results_list.append(link)
    for link in url_list:
        if link in results_list:
            continue
        results_list.append(link)
    # print(results_list)

    for link in results_list:
        if link in url_title:
            url = {}
            title = {}
            content = {}
            url["url"] = link
            title["title"] = url_title[link][0]
            content["content"] = url_title[link][1]
            results_dic[j] = (url, title, content)
            j = j + 1
        # print(results_dic)


def hits_main(arg1, arg2):
    read_json(arg1)
    read_crawl_list(arg2)
    build_adj_list()
    build_graph()
    hubs, authorities = calc_hits()
    build_results_dict(hubs, authorities)
    # print(hubs,authorities)
    print("hits output", results_dic)
    print("------")
    print(results_dic[1][1]['title'])
    sorted_d = dict(sorted(results_dic.items(), key=lambda x: x[1][1]['title']))
    with open(arg1 + "_hits_output.json", "w") as write_file:
        json.dump(results_dic, write_file)


if __name__ == '__main__':
    hits_main(sys.argv[1], sys.argv[2])
