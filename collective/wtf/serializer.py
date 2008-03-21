import csv

from zope.interface import implements
from zope.component import getUtility

from collective.wtf.interfaces import ICSVWorkflowSerializer
from collective.wtf.interfaces import ICSVWorkflowConfig

class DefaultSerializer(object):
    implements(ICSVWorkflowSerializer)

    def __call__(self, info, output_stream, config_variant=u""):
        """Given a dictified list of workflow info, wrote a CSV file.
        """
        
        config = getUtility(ICSVWorkflowConfig, name=config_variant)
        
        custom_roles = set()
        for s in info['state_info']:
            for p in s['permissions']:
                for r in p['roles']:
                    if r not in config.known_roles:
                        custom_roles.add(r)
        all_roles = config.known_roles + sorted(custom_roles)
    
        state_worklists = {}
        for w in info['worklist_info']:
            for v in w['var_match']:
                if v[0] == 'review_state':
                    state_worklists[v[1]] = w
    
        writer = csv.writer(output_stream)
    
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
                r(['Worklist:',                  w['description'].strip()          ])
                r(['Worklist label:',            w['actbox_name']                  ])
                r(['Worklist guard permission:', ', '.join(w['guard_permissions']) ])
                r(['Worklist guard role:',       ', '.join(w['guard_roles'])       ])
                r(['Worklist guard expression:', w['guard_expr']                   ])
        
            r(['Permissions', 'Acquire'] + all_roles)
        
            permission_map = dict([p['name'], p] for p in s['permissions'])
            ordered_permissions = [permission_map[p] for p in config.known_permissions if p in permission_map] + \
                                  [p for p in s['permissions'] if p['name'] not in config.known_permissions]

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
            r(['Description:',      t['title'].strip()                  ])
            r(['Details:',          t['description'].strip()            ])
            r(['Trigger:',          t['trigger_type'].capitalize()      ])
        
            r(['Guard permission:', ', '.join(t['guard_permissions'])   ])
            r(['Guard role:',       ', '.join(t['guard_roles'])         ])
            r(['Guard expression:', t['guard_expr']                     ])

            r([]) # terminator row