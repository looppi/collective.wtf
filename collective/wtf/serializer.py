import csv
from collective.wtf import config

def write_csv(info, output):
    """Given a dictified list of workflow info, wrote a CSV file.
    """
    custom_roles = set()
    for s in info['state_info']:
        for p in s['permissions']:
            for r in p['roles']:
                if r not in config.KNOWN_ROLES:
                    custom_roles.add(r)
    all_roles = config.KNOWN_ROLES + sorted(custom_roles)
    
    state_worklists = {}
    for w in info['worklist_info']:
        for v in w['var_match']:
            if v[0] == 'review_state':
                state_worklists[v[1]] = w
    
    writer = csv.writer(output)
    
    r = writer.writerow
    
    r(['[Workflow]'])
    r(['Id:',            info['id']                  ])
    r(['Title:',         info['title'].strip()       ])
    r(['Description:',   info['description'].strip() ])
    r(['Initial state:', info['initial_state']       ])
    r([]) # terminator row
    
    for s in info['state_info']:
        r(['[State]'])
        r(['Id:',           s['id']                     ])
        r(['Title:',        s['title'].strip()          ])
        r(['Description:',  s['description'].strip()    ])
        r(['Transitions',   ', '.join(s['transitions']) ])
        
        w = state_worklists.get(s['id'], None)
        if w is not None:
            r(['Worklist:',                  w['description']                  ])
            r(['Worklist label:',            w['actbox_name']                  ])
            r(['Worklist guard permission:', ', '.join(w['guard_permissions']) ])
            r(['Worklist guard role:',       ', '.join(w['guard_roles'])       ])
            r(['Worklist guard expression:', w['guard_expr']                   ])
        
        r(['Permissions', 'Acquire'] + all_roles)
        
        permission_map = dict([p['name'], p] for p in s['permissions'])
        ordered_permissions = [permission_map[p] for p in config.KNOWN_PERMISSIONS if p in permission_map] + \
                              [p for p in s['permissions'] if p['name'] not in config.KNOWN_PERMISSIONS]

        for p in ordered_permissions:
            acquired = 'N'
            if p['acquired']:
                acquired = 'Y'
            
            role_map = []
            for role in all_roles:
                if role in p['roles']:
                    role_map.append('Y')
                else:
                    role_map.append('N')
                
            r([p['name'], acquired] + role_map)
        
        r([]) # terminator row
        
    for t in info['transition_info']:
        r(['[Transition]'])
        
        r(['Id:',               t['id']                             ])
        r(['Target state:',     t['new_state_id']                   ])
        r(['Title:',            t['actbox_name']                    ])
        r(['Description:',      t['description'].strip()            ])
        r(['Trigger:',          t['trigger_type'].capitalize()      ])
        r(['Script before:',    t['script_name']                    ])
        r(['Script after:',     t['after_script_name']              ])
        
        r(['Guard permission:', ', '.join(t['guard_permissions'])   ])
        r(['Guard role:',       ', '.join(t['guard_roles'])         ])
        r(['Guard expression:', t['guard_expr']                     ])

        r([]) # terminator row