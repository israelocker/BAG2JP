"""Shared data-driven role adaptations and native predecessor dispatch."""
import json,struct,hashlib
from pathlib import Path
from animlib import info

def load_policy(path,project=None):
    policy=json.loads(Path(path).read_text(encoding='utf-8'))
    if policy.get('schema')!=1:raise ValueError('Unsupported animation policy')
    if project is not None:
        for item in policy.get("input_evidence",[]):
            if hashlib.sha256((Path(project)/item["file"]).read_bytes()).hexdigest()!=item["sha256"]:
                raise ValueError("Animation policy input changed; re-verify original tables")
    seen=set()
    for row in policy['roles']:
        if row['target'] in seen:raise ValueError('Duplicate target role')
        seen.add(row['target'])
        if not isinstance(row['target'],int) or not isinstance(row['source'],int) or row['target']<0 or row['source']<0:
            raise ValueError('Role indices must be nonnegative integers')
        if row['classification'] not in ('equivalent','adaptation') or not row.get('reason'):
            raise ValueError('Role requires classification and rationale')
    return policy

def native_variant(normal,previous,records):
    chosen=normal
    for start,alternate,prior_a,prior_b in records:
        if start==normal and previous in (prior_a,prior_b):chosen=alternate
    return chosen

def adapt_events(animation,rule):
    header,events,offset,end=info(animation);header=bytearray(header)
    if rule.get('hold'):
        if len(header)<6:raise ValueError('Animation cannot hold without a beat entry')
        header[5]=1
    additions=[tuple(event) for event in rule.get('required_events',[])]
    for event in additions:
        if len(event)!=3 or any(not isinstance(v,int) or not 0<=v<=65535 for v in event):
            raise ValueError('Invalid required animation event')
        if event[1]>=struct.unpack_from('<H',animation,4)[0]:raise ValueError('Event outside animation')
    events=events+[event for event in additions if event not in events]
    events.sort(key=lambda event:event[1])
    return animation[:offset]+header+b''.join(struct.pack('<HHH',*event) for event in events)+bytes(2)
