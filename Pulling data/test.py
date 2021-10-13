
def futures_process_fight_table(fights_list, graphql_endpoint, headers):
    session = FuturesSession(max_workers = 5)

    retries = 5
    status_forcelist = [429, 502]    
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        respect_retry_after_header=True,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    futures = [session.post(**get_fight_args(fight, graphql_endpoint, headers)) for fight in fights_list]

    player_list = []
    for q, future in enumerate(as_completed(futures)):
        if q % 100 == 0:
            print(f'Parsing {guild_name}, fight # {q+1} of {len(fights_list)}')
        result = future.result()
        if result.status_code != 200:
            print(result.status_code)
        table = result.json()['data']['reportData']['report']['table']['data']
        player_info = parse_fight_table(table, fights_list[q]['name'], fights_list[q]['unique_id'], guild_name)
        if len(player_list) == 0:
            player_list = player_info
        else:
            player_list.extend(player_info)
    return player_list, result

def make_batches(list_, n):
    new_list = []
    for k in range(0, len(list_), n):
        new_list.append(list_[k:k+n])
    return new_list

def batch_process_fight_table(fights_list, graphql_endpoint, headers):
    fight = fights_list[0]
    batches = make_batches(fights_list, 550)
    player_list = []
    last_time = datetime.datetime.now()
    for batch_num, batch_fight in enumerate(batches):

        result = requests.post(**get_fight_args(fight, graphql_endpoint, headers))
        if 'X-RateLimit-Remaining' in result.headers.keys() and int(result.headers['X-RateLimit-Remaining'])<550:
            print('At rate limit, wait longer.')
            time.sleep(60)

        print(f'Parsing batch # {batch_num}')
        plist, fut = futures_process_fight_table(batch_fight, graphql_endpoint, headers)
        # if 'X-RateLimit-Remaining' in fut.headers.keys() and int(fut.headers['X-RateLimit-Remaining'])<50:
        cur_time = datetime.datetime.now()
        time_diff = (cur_time - last_time).seconds
        print(f'Sleeping for {60-time_diff+3}.')
        for sleepy_time in range(60-time_diff+3):
            if sleepy_time % 10 == 0:
                print('\r', f'Slept for {sleepy_time}')
            time.sleep(1)
        last_time = datetime.datetime.now()
        player_list.extend(plist)
    return pd.DataFrame.from_dict(player_list)



def get_fight_table_and_parse(fights_list, graphql_endpoint, headers):
    
    player_list = []
    q = 0
    req_num = 0
    last_time = datetime.datetime.now()
    for fight in fights_list:
        print(q)
        # if time_diff < 50000:
        #     # print(time_diff)
        #     time.sleep(0.05 - (time_diff/1e6))
        result = requests.post(**get_fight_args(fight, graphql_endpoint, headers))
        if 'X-RateLimit-Remaining' in result.headers.keys() and int(result.headers['X-RateLimit-Remaining'])<50:
            cur_time = datetime.datetime.now()
            time_diff = (cur_time - last_time).microseconds
            print('Hit rate limit, sleeping for a sec.')
            time.sleep(60-(time_diff/1e6)+10)
            last_time = datetime.datetime.now()
        # last_time = datetime.datetime.now()
        if result.status_code!=200:
            time.sleep(5)
            print(result.status_code)
        else:
            cur_time = datetime.datetime.now()
        if result.status_code==429:
            print(result.status_code)
            time.sleep(10)
            result = requests.post(**get_fight_args(fight, graphql_endpoint, headers))
        try:
            table = result.json()['data']['reportData']['report']['table']['data']

            if q % 50 == 0:
                print(f'Parsing {guild_name}, fight # {q+1} of {len(fights_list)}')

            player_info = parse_fight_table(table, fights_list[q]['name'], fights_list[q]['unique_id'], guild_name)
            if len(player_list) == 0:
                player_list = player_info
            else:
                player_list.extend(player_info)
            q+=1
        except:
            pass

    return pd.DataFrame.from_dict(player_list)