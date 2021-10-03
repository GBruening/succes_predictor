
from requests_futures.sessions import FuturesSession
import os

def get_page_args(page_url):
    return {"url": page_url}

if os.path.exists('nysd-links.pkd'):
    link_list = dill.load(open('nysd-links.pkd', 'rb'))
else:
    print('Getting Links')
    session = FuturesSession(max_workers = 5)
    page1_url
    pages = []
    pages.extend([page1_url])
    for k in range(1,26):
        added_page = [page1_url+'?page='+str(k)]
        pages.extend(added_page)
    
    futures = [session.get(**get_page_args(pages[i])) for i in range(0,26)]
    link_list = [item for l in [get_links(future.result()) for future in futures] for item in l]

session = FuturesSession(max_workers = 10)

def make_query(log):
    log_id = log['code']
    query = """
    {
    reportData{
        report(code: "%s"){
        fights(difficulty: 5){
            name
            id
            averageItemLevel
            bossPercentage
            kill
            startTime
            endTime
        }
        }
    }
    }
    """ % (log_id)

    return query

def get_log_args(log, graphql_endpoint, headers):
    args = {'url': graphql_endpoint,
            'json': {'query': make_query(log)},
            'headers': headers}
    return args
futures = [session.post(**get_log_args(log, graphql_endpoint, headers)) for log in log_list]

for item in futures:
    fights = item.json()['data']['reportData']['report']['fights']
    for k, fight in enumerate(fights):
        fight

link_list = [item for l in [get_links(future.result()) for future in futures] for item in l]

log = log_list[56]
query = """
{
reportData{
    report(code: "%s"){
    fights(difficulty: 5){
        name
        id
        averageItemLevel
        bossPercentage
        kill
        startTime
        endTime
    }
    }
}
}
""" % (log_id)

r = requests.post(graphql_endpoint, json={"query": query}, headers=headers)
fight_list = r.json()['data']['reportData']['report']['fights']
for k in range(len(fight_list)):
    fight_list[k].update({'log_code': log_id})    
return fight_list