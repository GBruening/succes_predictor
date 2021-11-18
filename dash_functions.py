
def add_boss_nums(df):

    boss_names = [
        'Shriekwing', \
        'Huntsman Altimor',
        'Hungering Destroyer', \
        "Sun King's Salvation",
        "Artificer Xy'mox", \
        'Lady Inerva Darkvein', \
        'The Council of Blood', \
        'Sludgefist', \
        'Stone Legion Generals', \
        'Sire Denathrius']

    for k, item in enumerate(boss_names):
        df.loc[df.index[df['name'] == item],'boss_num'] = k
        
    return df

def make_agg_data_groupcomp(specific_boss):  
    specific_boss = specific_boss.replace("'", "''")
    
    curs.execute(f"select kill_df.unique_id, class as p_class, spec, role, \
        ilvl, covenant, boss_name \
        from nathria_prog_v2_players as players \
        join \
            (select * from max_pull_count_small \
            where name = '{specific_boss}' and kill = 'True') as kill_df \
        on players.unique_id = kill_df.unique_id;")
    sql_df = pd.DataFrame(curs.fetchall())
    sql_df.columns = [desc[0] for desc in curs.description]

    n_pulls = len(sql_df.unique_id.unique())
      
    df = sql_df
    df = df.dropna(subset = ['p_class','spec','role'])

    df['test'] = df[df.columns[1:4]].apply(
        lambda x: ', '.join(x.dropna().astype(str)),
        axis=1
    )

    temp_df = df.groupby(['unique_id','test']).\
        size().unstack(fill_value=0).stack().reset_index(name='counts')

    test = []
    for x in temp_df[temp_df.columns[1]]:
        test.append(re.findall('(.*),\s(.*),\s(.*)', str(x))[0][0])
    temp_df['p_class'] = temp_df[temp_df.columns[1]].apply(
        lambda x: re.findall('(.*),\s(.*),\s(.*)', str(x))[0][0]
    )
    temp_df['spec'] = temp_df[temp_df.columns[1]].apply(
        lambda x: re.findall('(.*),\s(.*),\s(.*)', str(x))[0][1]
    )
    temp_df['role'] = temp_df[temp_df.columns[1]].apply(
        lambda x: re.findall('(.*),\s(.*),\s(.*)', str(x))[0][2]
    )

    avg_comp = temp_df.groupby(['p_class','spec','role']).mean().reset_index().dropna().rename(columns={'counts': 'mean_val'})
    std_comp = temp_df.groupby(['p_class','spec','role']).std().reset_index().dropna().rename(columns={'counts': 'std_val'})
    std_comp['std_val'] = std_comp['std_val']/np.sqrt(n_pulls)

    df = pd.merge(avg_comp, std_comp, on=['p_class', 'spec'], how='inner').\
        rename(columns={'role_x': 'role'})

    df = df.reindex(columns=['p_class', 'spec', 'role', 'mean_val','std_val'])
    df['n_pulls'] = n_pulls

    return df

def make_comp_plot(specific_boss):
    df = make_agg_data_groupcomp(specific_boss)

    # df = df.groupby(['p_class', 'spec', 'role']).\
    #     size().\
    #     reset_index(name='counts')

    # avg_comp = df.\
    #     groupby(['p_class','spec','role']).\
    #     mean().reset_index().dropna().\
    #     rename(columns={'counts': 'mean_val'})
    # std_comp = df.\
    #     groupby(['p_class','spec','role']).\
    #     std().reset_index().dropna().\
    #     rename(columns={'counts': 'std_val'})
    # counts_comp = df.\
    #     groupby(['p_class','role','spec']).\
    #     sum().reset_index().dropna()
    # counts_comp.counts = counts_comp.counts/n_pulls
    # # df = pd.merge(avg_comp, std_comp, on=['p_class', 'spec'], how='inner').\
    # #     rename(columns={'role_x': 'role'}).query('role == "dps"')
        
    colors = {'DeathKnight': '#D62728',
            'DemonHunter': '#750D86',
            'Druid': '#F58518',
            'Hunter': '#54A24B',
            'Mage': '#17BECF',
            'Monk': '#22FFA7',
            'Paladin': '#FF97FF',
            'Priest': '#E2E2E2',
            'Rogue': '#EECA3B',
            'Shaman': '#3366CC',
            'Warlock': '#636EFA',
            'Warrior': '#8C564B'}

    bars = []
    for p_class in df['p_class'].unique():
        class_df = df.query(f"p_class == '{p_class}'")
        spec_count = 0
        specs = class_df['spec'].unique()
        if len(specs) == 2:
            offsets = [1,3]
        elif len(specs) == 1:
            offsets = [2]
        else:
            offsets = [0,2,4]
        for spec in specs:
            spec_df = class_df.query(f"spec == '{spec}'")
            bars.append(go.Bar(
                x = spec_df.p_class,
                y = spec_df.mean_val,
                # y = spec_df.counts,
                width = .15,
                error_y=dict(
                    type='data', 
                    array=[spec_df.std_val],
                    thickness=0.75),
                text = spec_df.spec,
                offsetgroup = spec_count,
                showlegend = False,
                marker = {'color': colors[p_class]}))
            # bars[-1].hoverlabel = spec
            spec_count += 1
    fig = go.FigureWidget(data=bars)
    fig['layout']['xaxis']['tickangle'] = -30
    fig['layout']['xaxis']['title'] = 'Player Class'
    fig['layout']['yaxis']['title'] = 'Average number of class/spec<br>in kill group (mean ± SD).'
    fig.update_traces(textposition='outside')
    fig.update_layout(
        template = 'plotly_dark',
        plot_bgcolor = 'rgba(0,0,0,255)',
        paper_bgcolor = 'rgba(0,0,0,255)',
        autosize=True,
        transition_duration = 500,
        font = dict(size = 12),
        uniformtext_minsize=4, 
        uniformtext_mode='show',
        showlegend = False,
        title_text=f'Approximate group composition<br>for {specific_boss}', 
        title_x=0.5
    )
    return fig




def filter_df(df_filter, metric):
    new_df_filt = pd.DataFrame()
    for boss_num in np.unique(df_filter['boss_num']):
        boss_df = df_filter.query('boss_num == '+str(boss_num))
        upper = np.quantile(boss_df[metric],.99)
        lower = np.quantile(boss_df[metric],.01)
        new_df_filt = new_df_filt.append(boss_df.query(str(metric)+ ' < '+str(upper)).query(str(metric)+ ' > '+str(lower)))
    return new_df_filt

def listify_pulls(end_perc2):
    pull_list = []

    n_fights = 10

    pulls_ml = [100]*n_fights
    for k in range(len(end_perc2)-1):
        if k == 0:
            pass
        else:
            pulls_ml.pop(0)
            pulls_ml.append(end_perc2[k])
        pull_list.append(pulls_ml.copy())
    return pull_list

def rm_repeat_boss(df):
    df = df.sort_values(by = ['fight_start_time'])
    temp_df = pd.DataFrame()
    temp_df = temp_df.append(df.iloc[0])

    last_start = df.iloc[0]['fight_start_time']
    last_perc = df.iloc[0]['boss_perc']
    for index, row in df[1:].iterrows():
        if abs(row['fight_start_time'] - last_start)/1000 > 30:
            if row['boss_perc'] > 0 and row['boss_perc'] != last_perc:
                temp_df = temp_df.append(row)
                last_start = row['fight_start_time']
                last_perc = row['boss_perc']
            elif row['boss_perc'] == 0:
                temp_df = temp_df.append(row)
                last_start = row['fight_start_time']
                last_perc = row['boss_perc']

    temp_df = temp_df.reset_index(drop = True)
    temp_df['pull_num'] = temp_df.index+1
    return temp_df

def get_one_guild_pulls(specific_boss, guild_name):
    specific_boss = specific_boss.replace("'", "''")
    curs2.execute(f"Select *, log_start+start_time as fight_start_time\
        from nathria_prog_v2 where name = '{specific_boss}' and guild_name = '{guild_name}';")

    pull_df = pd.DataFrame(curs2.fetchall())
    pull_df.columns = [desc[0] for desc in curs2.description]

    pull_df = rm_repeat_boss(pull_df)
    return pull_df

def make_fights_query_onefight(fight):
    code = fight['log_code']
    fight_ID = int(fight['id'])
    start_time = fight['start_time']
    end_time = fight['end_time']
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
            'json': {'query': make_fights_query_onefight(log)},
            'headers': headers}
    return args

def parse_fight_table(table, boss_name, unique_id, guild_name):

    comp = table['composition']
    roles = table['playerDetails']
    player_list = []
    for role in roles:
        players = roles[role]
        for player in players:
            try:
                gear_ilvl = [piece['itemLevel'] for piece in player['combatantInfo']['gear']]
                ilvl = np.mean(gear_ilvl)
            except:
                try:
                    ilvl = player['minItemLevel']
                except:
                    ilvl = np.NaN
            
            try:
                server = player['server']
                class_ = player['type']
            except:
                server = np.NaN
                class_ = np.NaN
            try:
                covenant = player['combatantInfo']['covenantID']
            except:
                covenant = np.NaN

            try:
                spec = player['specs'][0]
            except:
                spec = np.NaN

            try:
                stats = player['combatantInfo']['stats']
                primaries = ['Agility','Intellect','Strength']
                for primary in primaries:
                    if primary in stats.keys():
                        break
                primary= stats[primary]['min']
                mastery= stats['Mastery']['min']
                crit= stats['Crit']['min']
                haste= stats['Haste']['min']
                vers= stats['Versatility']['min']
                stamina= stats['Stamina']['min']
            except:
                primary = np.NaN
                mastery = np.NaN
                crit = np.NaN
                haste = np.NaN
                vers = np.NaN
                stamina = np.NaN
        
            player_info= {'unique_id': unique_id,
                        'player_name': player['name'],
                        'guild_name': guild_name,
                        'server': server,
                        'class': class_,
                        'spec': spec,
                        'role': role,
                        'ilvl': ilvl,
                        'covenant': covenant,
                        'primary': primary,
                        'mastery': mastery,
                        'crit': crit,
                        'haste': haste,
                        'vers': vers,
                        'stamina': stamina,
                        'boss_name': boss_name}
            player_list.append(player_info)
    return player_list
