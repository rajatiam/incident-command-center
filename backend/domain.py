import csv, hashlib, io, json, math, re
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from .validation import validate_input, http_url, unique

def now(): return datetime.now(timezone.utc).isoformat()
def validate(data,records): return initialize(validate_input(data,CONFIG['example']),records)

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
