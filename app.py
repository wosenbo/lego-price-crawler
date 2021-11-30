from flask import Flask, request, render_template, jsonify, redirect, url_for, make_response
import redis
from threading import Thread
import time
import json
import requests
import traceback as tb
from lxml import etree
from datetime import datetime
from const import *
from task import init_task, search_bricklink, search_lego

app = Flask(__name__, static_url_path='')
app.secret_key = 'XubjIYaO7ZCba2jhFK'
rdb = redis.StrictRedis('localhost', decode_responses=True)
threadList = []


@app.after_request
def cors(environ):
    environ.headers['Access-Control-Allow-Origin']='*'
    environ.headers['Access-Control-Allow-Method']='*'
    environ.headers['Access-Control-Allow-Headers']='x-requested-with,content-type'
    return environ


@app.route('/')
def auth():
    auth = request.cookies.get('lego_auth')
    if auth:
        try:
            if auth[4:-5] == ADMIN_PASS:
                return redirect(url_for('home'))
        except Exception as e:
            print(f'Password error: {e}')
    return app.send_static_file('auth.html')


@app.route('/login', methods=['POST'])
def login():
    pwd = request.form['password']
    if pwd != ADMIN_PASS:
        return 'Auth Failed'
    resp = make_response(redirect(url_for('home')))
    resp.set_cookie('lego_auth', 'hkzd'+ADMIN_PASS+'abcde', max_age=31536000)
    return resp


@app.route('/home')
def home():
    auth = request.cookies.get('lego_auth')
    if not auth:
        return redirect('/')
    if auth[4:-5] != ADMIN_PASS:
        return redirect('/')
    return app.send_static_file('index.html')


@app.route('/list')
def getList():
    site = request.args.get('site')
    if site not in SITES:
        return jsonify({'errcode': -1, 'errmsg': '未知站点'})
    items = []
    for item_id in rdb.smembers(f"legoList:{site}"):
        item = rdb.get(f"legoItem:{site}:{item_id}")
        if item is None:
            item = {'item_id': item_id, 'site': site, 'status': 0}
        else:
            item = json.loads(item)
        items.append(item)
    tasks = rdb.llen(f"legoTask:{site}")
    data = {
        'errcode': 0,
        'items': items,
        'tasks': tasks,
        'updateTime': rdb.get(f'legoUpdateTime:{site}')
    }
    if site == 'lego':
        data['regions_loc'] = REGIONS_LOC
    return jsonify(data)


@app.route('/add', methods=['post'])
def addItem():
    item_id = request.form['item_id']
    site = request.form['site']
    if site not in SITES:
        return jsonify({'errcode': -1, 'errmsg': '不支持的类型'})
    key = 'legoList:'+site
    if rdb.sismember(key, item_id):
        return jsonify({'errcode': -1, 'errmsg': '不能添加重复记录'})
    rdb.sadd(key, item_id)
    return jsonify({'errcode': 0, 'errmsg': ''})


@app.route('/del', methods=['post'])
def deleteItem():
    item_id = request.form['item_id']
    site = request.form['site']
    if site not in SITES:
        return jsonify({'errcode': -1, 'errmsg': '未知站点'})
    rdb.srem(f"legoList:{site}", item_id)
    rdb.delete(f"legoItem:{site}:{item_id}")
    return jsonify({'errcode': 0, 'errmsg': ''})


@app.route('/refresh')
def refresh():
    site = request.args.get('site')
    if site not in SITES:
        return jsonify({'errcode': -1, 'errmsg': '未知站点'})
    items = rdb.smembers(f"legoList:{site}")
    for item_id in items:
        item_key = f"legoItem:{site}:{item_id}"
        if not rdb.exists(item_key):
            continue
        row = json.loads(rdb.get(item_key))
        row['status'] = 0
        rdb.set(item_key, json.dumps(row))
    return jsonify({'errcode': 0, 'errmsg': '', 'tasks': len(items)})


def fetch_data():
    while 1:
        try:
            for site in SITES:
                task = rdb.lpop(f"legoTask:{site}")
                if not task:
                    time.sleep(5)
                    continue
                row = json.loads(task)
                print(f"Process task: {row}")
                if 'item_id' not in row or 'site' not in row:
                    raise Exception(f"Row error: {row}")
                rdb.set(f"legoUpdateTime:{site}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                item_key = f"legoItem:{row['site']}:{row['item_id']}"

                if row['site'] == 'bricklink':
                    detail = search_bricklink(row['item_id'])
                    if detail:
                        row['status'] = 6
                        row['detail'] = detail
                    else:
                        row['status'] = -1
                    rdb.set(item_key, json.dumps(row))
                elif row['site'] == 'lego':
                    if 'regions' not in row:
                        row['regions'] = {}
                        for region in REGIONS:
                            row['regions'][region] = None
                        rdb.set(item_key, json.dumps(row))
                    for region in REGIONS:
                        detail = search_lego(row['item_id'], region)
                        if detail:
                            row['status'] = 6
                            if 'name' not in row or row['name'] == '':
                                row['name'] = detail['name']
                        row['regions'][region] = detail
                        rdb.set(item_key, json.dumps(row))
                    if row['status'] != 6:
                        row['status'] = -1
                        rdb.set(item_key, json.dumps(row))
        except Exception as e:
            print(f"Task error: {e}")
            tb.print_exc()


def query_task():
    while 1:
        init_task(rdb)
        time.sleep(5)


def main():
    for i in range(MAX_THREAD_NUM):
        th = Thread(target=fetch_data)
        th.daemon = True
        th.start()
        threadList.append(th)

    producer = Thread(target=query_task)
    producer.daemon = True
    producer.start()

    try:
        app.run(host='0.0.0.0')
    except KeyboardInterrupt:
        producer.cancel()
        for i in range(MAX_THREAD_NUM):
            threadList[i].cancel()


if __name__ == '__main__':
    main()
