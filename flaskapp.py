from flask import Flask, request
from flask_cors import CORS
from urllib.request import urlopen
import simplejson
import json
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import os
from project_hits_read import hits_main
from KMeans_Clustering import kmeans_main
from Agglomerative_Clustering import agglo_main

app = Flask(__name__)
CORS(app)


@app.route("/")
def home():
    return "Food Recipe Query App"

@app.route("/index")    
@app.route('/query', methods=['GET', 'POST'])
def query():
    if request.method == 'POST' or request.method == 'GET':
        file = open("query.txt", "a")
        text = request.args.get('mydata')
        callback = request.args.get('callback')
        rows = 0
        file.write(str(text)+'\n')
        file.close()
        data = fetch_from_solr()
        '''google_data = fetch_from_google(text)
        bing_data = fetch_from_bing(text)
        json_data = {
            'google': google_data,
            'bing': bing_data
        }

        response = app.response_class(
            response=json.dumps(json_data),
            mimetype='application/json'
        )'''
        response = app.response_class(
            response=data,
            mimetype='application/json'
        )
        return response


@app.route('/solr', methods=['GET','POST'])
def fetch_from_solr():
    input_string = request.args.get('mydata')
    start = 1
    if os.path.exists(str(input_string) + ".txt"):
        with open(str(input_string) + ".txt", 'r', encoding="utf8") as f:
            response = json.load(f)
    else:
        input_string = str(input_string).replace(" ", "%20")
        connection = urlopen('http://localhost:8983/solr/nutch/select?fl=*%2C%20score&q=content:\"' + input_string +
                             '\"&rows=' + str(start+70) + '&sort=score%20desc&start=' + str(start) + '&wt=json')
        print(connection)
        response = simplejson.load(connection)
        no_of_docs = int(response["response"]["numFound"])
        print("Number of results returned : " + str(no_of_docs))
        with open(input_string + '.txt', 'w') as output_file:
            json.dump(response, output_file)
    return response


@app.route('/google', methods=['GET', 'POST'])
def fetch_from_google():
    ua = UserAgent()
    number_result = 20
    input_string = request.args.get('mydata')
    google_url = "https://www.google.com/search?q=" + input_string + "&num=" + str(number_result)
    response = requests.get(google_url, {"User-Agent": ua.random})
    soup = BeautifulSoup(response.text, "html.parser")

    result_div = soup.find_all('div', attrs={'class': 'ZINbbc'})
    results = []
    links = []
    titles = []
    descriptions = []

    for r in result_div:
        # Checks if each element is present, else, raise exception
        try:
            link = r.find('a', href=True)
            title = r.find('div', attrs={'class': 'vvjwJb'}).get_text()
            description = r.find('div', attrs={'class': 's3v9rd'}).get_text()

            # Check to make sure everything is present before appending
            if link != '' and title != '' and description != '':
                # links.append(link['href'])
                # titles.append(title)
                # descriptions.append(description)
                results.append({
                    'link': link['href'][7:],
                    'title': title,
                    'snippet': description})
        # Next loop if one element is not present
        except:
            continue

    response = app.response_class(
        response=json.dumps(results),
        mimetype='application/json'
    )
    return response


@app.route('/bing', methods=['GET', 'POST'])
def fetch_from_bing():
    input_string = request.args.get('mydata')
    print(input_string)
    address = "http://www.bing.com/search?q=%s" % (input_string)
    response = requests.get(address, {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0'})
    soup = BeautifulSoup(response.text, 'html.parser')

    [s.extract() for s in soup('span')]
    unwantedTags = ['strong', 'cite']
    for tag in unwantedTags:
        for match in soup.findAll(tag):
            match.replaceWithChildren()

    result_div = soup.findAll('li', {"class": "b_algo"})

    results = []
    print(len(result_div))
    for result in result_div:

        try:
            link = result.find('h2').find('a', href=True)['href']
            title = result.find('h2').get_text()
            description = result.find('p').get_text()
            results.append({
                'link': link,
                'title': title,
                'snippet': description
            })

        except:
            continue

    response = app.response_class(
        response=json.dumps(results),
        mimetype='application/json'
    )
    return response


@app.route('/hits', methods=['GET', 'POST'])
def hits():
    input_string = request.args.get('mydata')
    hits_main(input_string, "crawl.txt")
    input_string = input_string.replace(" ", "%20")
    f = open(input_string + ".txt", encoding="utf-8")
    data = json.load(f, strict=False)
    response = app.response_class(
        response=json.dumps(data),
        mimetype='application/json'
    )
    return response


@app.route('/kmeans', methods=['GET', 'POST'])
def kmeans():
    input_string = request.args.get('mydata')
    kmeans_main(input_string)
    input_string = input_string.replace(" ", "%20")
    f = open(input_string + ".txt", encoding="utf-8")
    data = json.load(f, strict=False)
    response = app.response_class(
        response=json.dumps(data),
        mimetype='application/json'
    )
    return response


@app.route('/agglo', methods=['GET', 'POST'])
def agglo():
    input_string = request.args.get('mydata')
    agglo_main(input_string)
    input_string = input_string.replace(" ", "%20")
    f = open(input_string + ".txt", encoding="utf-8")
    data = json.load(f, strict=False)
    response = app.response_class(
        response=json.dumps(data),
        mimetype='application/json'
    )
    return response


'''
@app.route('/rocchio', methods=['GET', 'POST'])
def rocchio(input_string):
    rocchio_main(input_string)
    
@app.route('/rocchio', methods=['GET', 'POST'])
def rocchio(input_string):
    rocchio_main(input_string)
'''

if __name__ == "__main__":
    app.run(debug=True)
