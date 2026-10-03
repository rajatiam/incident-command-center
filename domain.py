import csv, hashlib, io, json, math, re
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def now(): return datetime.now(timezone.utc).isoformat()

def validate(data, records):
    if not isinstance(data,dict): raise ValueError('JSON object required')
    row = {}
    for key,example in CONFIG['example'].items():
        value = data.get(key)
        if isinstance(example,bool):
            if not isinstance(value,bool): raise ValueError(key+' must be boolean')
        elif isinstance(example,(int,float)):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0: raise ValueError(key+' must be finite and nonnegative')
            if isinstance(example,int) and not isinstance(value,int): raise ValueError(key+' must be an integer')
        elif not isinstance(value,str) or not value.strip() or len(value)>2000: raise ValueError(key+' requires text, up to 2000 characters')
        row[key] = value.strip() if isinstance(value,str) else value
    return initialize(row,records)

def http_url(value):
    url = urlparse(value)
    if url.scheme not in ['http','https'] or not url.hostname or url.username or url.password: raise ValueError('HTTP(S) URL without credentials required')

def unique(rows,row,fields):
    if any(all(r[f]==row[f] for f in fields) for r in rows): raise ValueError('Duplicate '+', '.join(fields))

def initialize(row,records):
    if row['severity'] not in ['low','medium','high','critical']: raise ValueError('Invalid severity')
    return dict(row,status='open',opened_at=now(),acknowledged_at=None,resolved_at=None,resolution_seconds=None)
def summary(rows):
    durations=[r['resolution_seconds'] for r in rows if r['resolution_seconds'] is not None]
    return {'incidents':len(rows),'active':sum(r['status']!='resolved' for r in rows),'resolved':len(durations),'mean_resolution_seconds':round(sum(durations)/len(durations),2) if durations else 0}
def transition(row,action):
    if action=='acknowledge' and row['status']=='open': return dict(row,status='acknowledged',acknowledged_at=now())
    if action=='resolve' and row['status']=='acknowledged':
        end=now(); seconds=max(0,(datetime.fromisoformat(end)-datetime.fromisoformat(row['opened_at'])).total_seconds())
        return dict(row,status='resolved',resolved_at=end,resolution_seconds=round(seconds,3))
    raise ValueError('Acknowledge an open incident before resolving it')
