# postman_collection

## what it is

a Postman collection (v2.1 JSON) with 29 requests and 60 test assertions for the local reqres.in clone https://github.com/ClasherGeek77/reqresin_clone. it is the Postman port of https://github.com/ClasherGeek77/bruno_collection: same folders, same requests, same checks.

folders: `USERS` (8), `RESOURCES` (3), `PRODUCTS` (1), `AUTH` (4), `EXTRAS` (7), `CHAIN` (6, create -> read back -> update -> delete -> read back again, values passed between requests with `pm.variables.set`).

there is no Postman environment file. the collection carries its own variables: `base_url` (`http://localhost:40000`), and `plan_name`, `plan_job`, `new_user_id` for the chain.

## when to use it

- to learn Postman collections, tests and chained requests on an API you can run locally.
- to click through the clone's API, or run all checks with `newman` on the command line.

when not to use it:

- if you use Bruno, use https://github.com/ClasherGeek77/bruno_collection: that is the source, and its files are plain text.
- for an automated suite with reports, use https://github.com/ClasherGeek77/pytest_api_boilerplate or https://github.com/ClasherGeek77/katalon_api_boilerplate.
- this collection targets the clone, not the live https://reqres.in/: the CHAIN folder relies on the clone's fixed id `4` and its statelessness.

## what you need

- Postman desktop app (any current version; not tested against a specific one): https://www.postman.com/downloads/
- the reqres clone running on port 40000 (below), with python 3.8 or newer.
- for the command line only: `newman` (version 6.2.1 verified) and node/npm.

## quick start

1. start the clone and leave it running:

```bash
git clone https://github.com/ClasherGeek77/reqresin_clone.git
cd reqresin_clone
python3 server.py
```

you should see `reqres clone on http://localhost:40000/api  (Ctrl-C to stop)`.

2. get this collection:

```bash
git clone https://github.com/ClasherGeek77/postman_collection.git
```

3. in Postman: Import -> choose `reqres_clone.postman_collection.json`.
4. environment: none. leave the environment selector on "No Environment"; `base_url` comes from the collection variables.
5. open `USERS` -> `Single user` -> Send. you should see `200 OK` with `"first_name": "Janet"`, and in the Test Results tab all tests passed.

to run everything: right-click the collection `reqres_clone` -> Run collection -> Run. you should see 29 requests and 60 passed tests. keep the order of the `CHAIN` folder.

## run from the command line

```bash
newman run reqres_clone.postman_collection.json
```

(install with `npm install -g newman` if the command is missing; not run here, only the installed 6.2.1 was verified.) you should see each folder and request with its status and a tick per test, ending with a table:

```
requests               29 executed   0 failed
test-scripts           29 executed   0 failed
assertions             60 executed   0 failed
```

one folder only: `newman run reqres_clone.postman_collection.json --folder CHAIN`

other port: `newman run reqres_clone.postman_collection.json --env-var base_url=http://localhost:8000`

## how to read the code

- `reqres_clone.postman_collection.json`: the collection. generated, do not edit by hand.
- `scripts/port.py`: regenerates the JSON from the `.bru` files of the Bruno collection. it parses them with `@usebruno/lang` (node) and rewrites the scripts: `bru.setVar` -> `pm.variables.set`, `res.getStatus()` -> `pm.response.code`, `res.getBody()` -> `pm.response.json()`, `expect`/`test` -> `pm.expect`/`pm.test`. by default it reads `../bruno_collection/reqres` (a clone of https://github.com/ClasherGeek77/bruno_collection next to this one) and expects the node module in `~/.local/node_modules/@usebruno/lang`; override with `BRUNO_COLLECTION=<path>` and `USEBRUNO_LANG=<path>`. most readers never need it.
- URLs in the JSON are plain strings on purpose: an object URL with an empty `query` array shadows the raw string in newman.

## if it breaks

| symptom | cause | fix |
| --- | --- | --- |
| every request: `Could not get response` / `ECONNREFUSED 127.0.0.1:40000` | the clone is not running | start it: `python3 server.py` in `reqresin_clone` |
| request URL is `{{base_url}}/...` and fails | the variable was not loaded (collection not imported properly) or overwritten by an environment with an empty `base_url` | re-import the JSON; select "No Environment" |
| `newman: command not found` | newman not installed | `npm install -g newman` |
| a CHAIN request fails alone | it needs the previous request's variable | run the whole CHAIN folder in order |
| `Delayed response` takes about 1 second | it asks the clone for `?delay=1` | expected |

## next

- the same requests in Bruno (plain text, source of this port): https://github.com/ClasherGeek77/bruno_collection
- the API under test: https://github.com/ClasherGeek77/reqresin_clone
- API tests as code: https://github.com/ClasherGeek77/pytest_api_boilerplate and https://github.com/ClasherGeek77/katalon_api_boilerplate
