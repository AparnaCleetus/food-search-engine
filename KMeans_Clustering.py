import json
import os
import sys
from urllib.request import urlopen

import pandas as pd
import project_hits_read
import simplejson
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer


def get_document_data(crawl_file):
    print("****************** Reading documents ******************")
    crawl_file = crawl_file.replace(" ", "%20")
    if os.path.exists(crawl_file+".txt"):
        with open(crawl_file+".txt", encoding="utf-8") as file:
            file_content = json.loads(file.read())
    else:
        connection = urlopen('http://localhost:8983/solr/nutch/select?fl=*%2C%20score&q=content:\"' +
                             crawl_file + '\"&rows=' + str(70) +
                             '&sort=score%20desc&start=' + str(0) + '&wt=json')
        file_content = simplejson.load(connection)
        with open(crawl_file+".txt", 'w') as output_file:
            json.dump(file_content, output_file)

    url_content_dict = {}
    url_title = {}
    response = file_content['response']['docs']
    for item in response:
        key = str(item['url']).replace('[', '').replace(']', '').replace('\'', '')
        if 'content' in item.keys() and 'title' in item.keys():
            value = str(item['content']).replace('\\n', ' ').replace('[', '').replace(']', '')
            url_content_dict[key] = value

            value = str(item['title']).replace('[', '').replace(']', '')
            url_title[key] = value

    data = pd.DataFrame({
        'url': list(url_content_dict.keys()),
        'title': list(url_title.values()),
        'content': list(url_content_dict.values()),
    })

    return data


def get_ranked_doc(query):
    print("****************** Getting high ranked page ******************")
    if os.path.exists(query + '_hits_output.json'):
        with open(query + '_hits_output.json') as file:
            hits_response = json.loads(file.read())
    else:
        print("Calling HITS algortihm")
        project_hits_read.hits_main(query, 'crawl.txt')
        with open(query + '_hits_output.json') as file:
            hits_response = json.loads(file.read())

    high_ranked_docs = []

    # get top web pages from HITS and load it into a Dataframe
    for key, value in hits_response.items():
        high_ranked_docs.append(value[0]['url'])

    return pd.DataFrame({
        'url': high_ranked_docs
    })


def call_kmeans(data):
    print("****************** Building Kmeans distance ******************")
    tf_idf_vectorizer = TfidfVectorizer(stop_words='english',
                                        max_df=0.8,
                                        min_df=0.2,
                                        ngram_range=(1, 3))
    tfidf_matrix = tf_idf_vectorizer.fit_transform(data['content'])

    true_k = 14
    model = KMeans(n_clusters=true_k, init='k-means++', max_iter=100, n_init=1)
    model.fit(tfidf_matrix)

    df = pd.DataFrame({
        'url': data['url'],
        'title': data['title'],
        'cluster': model.labels_.tolist(),
        'content': data['content']
    })
    return df

'''
def return_result(df, ranked_doc, output_file):
    # Merge top documents on column url
    result = pd.merge(df, ranked_doc, on=['url'])

    # group by cluster and count members of each group
    result = result.groupby(['cluster']).count()

    # pick the group with max count
    max_count = result['url'].max()

    # get the cluster with max_count
    cluster = result.index[result['url'] == max_count][0]

    result = df[df['cluster'] == cluster]
    result = result.drop(columns=['cluster'])

    result.to_json(output_file, orient="index")
'''


def return_result(df, ranked_doc, output_file):
    print("df " + str(df['url'].iloc[0]))
    print("ranked : ", str(ranked_doc['url'].iloc[0]))
    high_ranked_url = ranked_doc['url'].iloc[0]
    print(high_ranked_url)
    print("Result : " + str(df[df['url'] == high_ranked_url]))

    high_ranked_cluster = df[df['url'] == high_ranked_url]
    print(high_ranked_cluster)

    high_ranked_cluster = high_ranked_cluster['cluster'].iloc[0]
    print("cluster pages", str(high_ranked_cluster))

    result = df[df['cluster'] == high_ranked_cluster]
    print("final result ", str(result))
    result = result.drop(columns=['cluster'])

    #print(high_ranked_cluster["cluster"])
    #high_ranked_cluster = high_ranked_cluster['cluster']
    #print(high_ranked_cluster)

    #esult = df[df['cluster'] == high_ranked_cluster]
    #result = result.drop(columns=['cluster'])

    result.to_json(output_file, orient="index")


def kmeans_main(argv1):
    ranked_doc = get_ranked_doc(argv1)
    data = get_document_data(argv1)

    kdata = call_kmeans(data)

    return_result(kdata, ranked_doc, "Kmeans_" + argv1 + ".json")


if __name__ == "__main__":
    kmeans_main(sys.argv[1])
