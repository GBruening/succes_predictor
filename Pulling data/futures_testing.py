
from requests_futures.sessions import FuturesSession
import os

session = FuturesSession(max_workers = 10)

def make_logs_query(log):
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
            'json': {'query': make_logs_query(log)},
            'headers': headers}
    return args

def get_fight_list(log_list, graphql_endpoint, headers):
    futures = [session.post(**get_log_args(log, graphql_endpoint, headers)) for log in log_list]

    fights_list = []
    for q, item in enumerate(futures):
        fights = item.result().json()['data']['reportData']['report']['fights']
        for k, fight in enumerate(fights):
            fight['code'] = log_list[q]['code']
            fight['log_start'] = log_list[q]['startTime']
            fight['log_end'] = log_list[q]['endTime']
            fight['unique_id'] = log_list[q]['code'] + '_' + str(fight['id'])
            fights_list.extend([fight])
    
    return fights_list

def make_fights_query(fight):
    code = fight['code']
    fight_ID = fight['id']
    start_time = fight['startTime']
    end_time = fight['endTime']
    query = """
    {
    reportData{
        report(code: "%s"){
        table(fightIDs: %s, startTime: %s, endTime: %s)
        }
    }
    }
    """ % (code, fight_ID, str(start_time), str(end_time))

    return query

def get_fight_args(log, graphql_endpoint, headers):
    args = {'url': graphql_endpoint,
            'json': {'query': make_fights_query(log)},
            'headers': headers}
    return args

def get_fight_table(fights_list, graphql_endpoint, headers):
    futures = [session.post(**get_fight_args(fight, graphql_endpoint, headers)) for fight in fights_list]

    


