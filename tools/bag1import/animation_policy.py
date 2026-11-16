"""Shared data-driven role adaptations and native predecessor dispatch."""
import json,struct,sys
from pathlib import Path
from animlib import info

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.workflow.project_config import ConfigError, load_config  # noqa: E402
from character_workflow import file_sha, resolve_declared_input  # noqa: E402

def load_policy(path,project=None,config=None):
    """Load an animation policy; declared evidence resolves through configuration.

    ``input_evidence`` entries name project-relative locations whose leading
    ``_work`` component means the configured work root. The policy bytes, roles and
    native mappings stay authoritative; only the host location comes from config.
    Evidence is never skipped when a project is omitted: that is refused instead.
    """
    policy=json.loads(Path(path).read_text(encoding='utf-8'))
    if policy.get('schema')!=1:raise ValueError('Unsupported animation policy')
    evidence=policy.get("input_evidence",[])
    if project is None:
        if config is not None:
            raise ValueError('Policy configuration requires the project it belongs to')
        if evidence:
            raise ValueError('Policy input evidence requires a project and its configuration')
    else:
        project=Path(project)
        config=config if config is not None else load_config(repo_root=project)
        if config.repo_root!=project.resolve():
            raise ConfigError('Policy configuration belongs to a different project')
        for item in evidence:
            target=resolve_declared_input(project,config,item["file"])
            if file_sha(target)!=item["sha256"]:
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
