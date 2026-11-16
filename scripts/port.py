#!/usr/bin/env python3
"""Port the Bruno collection (ClasherGeek77/bruno_collection) to Postman v2.1 JSON.

Regenerates reqres-clone.postman_collection.json from the .bru files, parsing each
with the same @usebruno/lang@0.12 the Bruno GUI uses, and translating the JS:

    bru.setVar(k, v)              -> pm.variables.set(k, v)
    res.getStatus()               -> pm.response.code
    res.getBody()                 -> pm.response.json()
    res.headers["k"]              -> pm.response.headers.get("k")
    expect(...) / test(...)       -> pm.expect / pm.test

URLs are emitted as plain strings — an object url with an empty query[] would
shadow the raw string in newman (learned the hard way).

Requires: node + ~/.local/node_modules/@usebruno/lang (pinned versions).
"""
import json
import os
import re
import subprocess

SRC = os.path.expanduser('~/Documents/github_clashergeek77/bruno_collection/reqres')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'reqres-clone.postman_collection.json')
GROUPS = ['USERS', 'RESOURCES', 'PRODUCTS', 'AUTH', 'EXTRAS', 'CHAIN']
LANG = os.path.expanduser('~/.local/node_modules/@usebruno/lang')


def parse(path):
    js = 'process.stdout.write(JSON.stringify(require("%s").bruToJsonV2(require("fs").readFileSync(process.argv[1],"utf8"))))' % LANG
    out = subprocess.run(['node', '-e', js, path], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit('lang parse failed for %s: %s' % (path, out.stderr[:200]))
    return json.loads(out.stdout)


def js_convert(src):
    src = re.sub(r'\bbru\.setVar\(', 'pm.variables.set(', src)
    src = src.replace('res.getBody()', 'pm.response.json()')
    src = src.replace('res.getStatus()', 'pm.response.code')
    src = re.sub(r'res\.headers\["([^"]+)"\]', r'pm.response.headers.get("\1")', src)
    src = re.sub(r'(?<!pm\.)\bexpect\(', 'pm.expect(', src)
    src = re.sub(r'(?<!pm\.)\btest\(', 'pm.test(', src)
    return src


def request_item(path):
    p = parse(path)
    h = p.get('http') or {}
    body = p.get('body') or {}
    meta = p.get('meta') or {}
    varsd = p.get('vars') or {}
    script = p.get('script') or {}
    headers = [{'key': x['name'], 'value': x.get('value', ''), 'disabled': not x.get('enabled', True)}
               for x in (p.get('headers') or [])]
    item = {
        'name': meta.get('name') or os.path.basename(path),
        'request': {
            'method': (h.get('method') or 'get').upper(),
            'header': headers,
            'url': h.get('url', ''),  # plain string: empty query[] shadows raw
            'description': 'ported from the Bruno collection',
        },
        '_seq': int(meta.get('seq') or 999),
    }
    mode = body.get('mode') or ('json' if 'json' in body else 'none')
    if mode == 'json' and body.get('json'):
        item['request']['body'] = {'mode': 'raw', 'raw': body['json'], 'options': {'raw': {'language': 'json'}}}
        if not any(x['key'].lower() == 'content-type' for x in headers):
            item['request']['header'].insert(0, {'key': 'Content-Type', 'value': 'application/json'})
    pre = ['pm.variables.set("%s", "%s");' % (v['name'], v['value']) for v in varsd.get('req', [])]
    if script.get('req'):
        pre.insert(0, js_convert(script['req']))
    post = []
    for v in varsd.get('res', []):
        m = re.match(r'\{\{res\.body\.(.+?)\}\}', str(v.get('value', '')))
        post.append('pm.variables.set("%s", %s);' % (v['name'],
                    'pm.response.json().%s' % m.group(1) if m else json.dumps(v['value'])))
    if script.get('res'):
        post.append(js_convert(script['res']))
    if p.get('tests'):
        post.append(js_convert(p['tests']))
    ev = []
    if pre:
        ev.append({'listen': 'prerequest', 'script': {'type': 'text/javascript', 'exec': '\n'.join(pre).splitlines()}})
    if post:
        ev.append({'listen': 'test', 'script': {'type': 'text/javascript', 'exec': '\n'.join(post).splitlines()}})
    if ev:
        item['event'] = ev
    return item


def main():
    groups = {}
    for g in GROUPS:
        d = os.path.join(SRC, g)
        if not os.path.isdir(d):
            continue
        items = sorted((request_item(os.path.join(d, f)) for f in os.listdir(d) if f.endswith('.bru')),
                       key=lambda x: x['_seq'])
        groups[g] = [{k: v for k, v in it.items() if k != '_seq'} for it in items]
    coll = {
        'info': {
            'name': 'reqres-clone',
            'description': ('Ported 1:1 from the Bruno collection (ClasherGeek77/bruno_collection). '
                            'Exercises the local stateless reqres clone (http://localhost:40000). '
                            'CHAIN folder ports bru.setVar -> pm.variables.set; run folders in order.'),
            'schema': 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
        },
        'item': [{'name': g, 'item': groups[g]} for g in GROUPS if groups.get(g)],
        'variable': [
            {'key': 'base_url', 'value': 'http://localhost:40000', 'type': 'string'},
            {'key': 'plan_name', 'value': 'chain-morpheus', 'type': 'string'},
            {'key': 'plan_job', 'value': 'chain-leader', 'type': 'string'},
            {'key': 'new_user_id', 'value': '4', 'type': 'string'},
        ],
    }
    with open(OUT, 'w') as f:
        json.dump(coll, f, indent=2)
    print('wrote %s: %d requests in %d folders' % (OUT, sum(len(v) for v in groups.values()), len(groups)))


if __name__ == '__main__':
    main()
