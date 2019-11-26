import requests
import datetime, time
import random
import json
import os.path
import openpyxl
import logging
import urllib
import base64
import pandas as pd
import pytest

logger = logging.getLogger('logger')


class GetParams(object):

    @staticmethod
    def generate_date_range(rand_params, dt_from, dt_to):

        dt_list = pd.date_range(dt_from, dt_to)
        delta_days = 31
        date_to = dt_list[-1]

        if rand_params:
            date_to = random.choice(dt_list)
            delta_days = random.randint(0, len(pd.date_range(dt_from, dt_to)))

        date_from = max(date_to - datetime.timedelta(days=delta_days), dt_list[0])
        prev_date_to = date_from - datetime.timedelta(days=1)
        prev_date_from = prev_date_to - datetime.timedelta(days=delta_days)

        date_range_random = {
            'date_to': date_to.strftime('%d-%m-%Y'),
            'date_from': date_from.strftime('%d-%m-%Y'),
            'prev_date_to': prev_date_to.strftime('%d-%m-%Y'),
            'prev_date_from': prev_date_from.strftime('%d-%m-%Y'),
        }

        return date_range_random

    @staticmethod
    def generate_metrics(get_defaults, urls, func, rand=None, method=None, data=None, default=None):
        rand = rand if rand is not None else get_defaults
        req_params = {
            'url': get_defaults['parent_url'] + urls,
            'headers': get_defaults['headers'],
            'timeout': 120 * 2
        }
        if data:
            req_params['data'] = json.dumps(data)
        response = getattr(requests, method)(**req_params)

        metric_ids = func(response)

        if rand.get('random_filters') and metric_ids:
            metric_ids = random.sample(metric_ids, random.randint(*sorted([1, min(21, len(metric_ids))])))
        logger.info({'urls': urls, 'method': method, 'metrics': metric_ids})

        return default if default is not None and not rand.get('random_filters') else metric_ids

    @staticmethod
    def generate_rand_choise(get_defaults, params_list=None):

        params_list = params_list if params_list else [False, True]
        if len(params_list) > 1 and get_defaults.get('random_filters'):
            metrics = random.choice(params_list)
        else:
            metrics = params_list[0]

        return metrics

    @staticmethod
    def choice_rnd(get_defaults, params_tsa):
        if params_tsa == 'Random':
            rand = {'random_filters': random.choice([True, False])}
        elif params_tsa == 'Rnd values':
            rand = {'random_filters': True}
        elif params_tsa == 'Default':
            rand = {}
        else:
            rand = get_defaults
        return rand


class GenerateFiles(object):

    @staticmethod
    def update_settings(data=None):
        base_setings = {
            'users': {
                'name': 'key'
            },
            'hosts': [
                "http://127.0.0.1:8000",
            ],
            'reports': {
                'ANALITICS': {
                    'shops_sales': '',                    
                },
                'VIZUALIZATIONS': {
                    'drill_down': '',
                },
                'SPECIAL': {
                    'meteor_products': '',                  
                },                
            },
            'params_base': {
                'shops': ['Rnd values'],
                'group_level': ['Rnd values'],
                'categories': ['Rnd values'],
                'date_range': ['Rnd values'],
                'date_range_future': ['Rnd values'],
                'markers': ['Rnd values'],
                'receipt_markers': ['Rnd values'],             
            },
            'params_choice': {
                'interval': ['day', 'week', 'month'],
                'group_by_level': ['categories', 'brands'],
                'group_by_level_quadrant': ['products', 'brands', 'producers'],                
                'selected_report_level': ['product', 'category', 'manager'],
                'time_from': [f'{x:02d}:00' for x in range(24)],
                'time_to': [f'{x:02d}:00' for x in range(24)],
                'level': [str(x) for x in range(20)],
                'count_month': [str(x) for x in range(1, 13)],
                'group_count': ['3', '5'],               
            },
            'params_bool': {
                'filter_x': ['True', 'False'],
                'main_products': ['True', 'False'],
                'drop_sale_products': ['True', 'False'],
                'like_for_like': ['True', 'False'],
                'any_stock_null': ['True', 'False'],
                'group_by_suppliers': ['True', 'False'],
                'new_clients': ['True', 'False'],
                'anomaly': ['True', 'False'],
                'active_last_sale': ['True', 'False'],
            },
            'params_testing': {
                'random_filters': ['Default', 'Random'],
                'tree_ajax': ['Not open', 'Open'],
            }
        }
        settings_tas = data if data else base_setings
        settings_file = 'settings_TAS'
        available_settings = os.path.isfile(settings_file)
        if available_settings and not data:
            with open(settings_file, 'r+') as f:
                settings_tas = json.loads(f.read())
                change_params =[k for k in ['reports', 'params_base', 'params_choice',
                                            'params_bool', 'params_testing'] if settings_tas[k]!=base_setings[k]]
                if change_params:
                    for k in change_params:
                        settings_tas.update({k:base_setings[k]})
                    f.seek(0)  # rewind
                    json.dump(settings_tas, f, ensure_ascii=False, indent=4)
                    f.truncate()
        else:
            with open('settings_TAS', 'w', encoding='utf-8') as f:
                json.dump(settings_tas, f, ensure_ascii=False, indent=4)

        return settings_tas

    @staticmethod
    def results_to_excel(result, name):

        directory = f'./testing_results_{datetime.date.today().strftime("%d-%m-%Y")}/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        file = directory + f"test_{result['user_name']}.xlsx"

        if name == 'pytest':
            file = directory + "test_pytest.xlsx"

        columns = ["time",
                   "test_name",
                   "user_name",
                   "duration",
                   "outcome",
                   "error",
                   "params",
                   'urls_requests',
                   "params_url",
                   "random",
                   ]

        df = pd.DataFrame(columns=columns)
        available_file = os.path.isfile(file)

        if available_file:
            book = openpyxl.load_workbook(file)
            sheets = dict((ws.title, ws) for ws in book.worksheets)
            if name in sheets:
                df = pd.read_excel(file, sheet_name=name)

        df = df.append(result, ignore_index=True)

        if available_file:
            with pd.ExcelWriter(file, engine="openpyxl") as writer:
                writer.book = book
                writer.sheets = sheets

                df.to_excel(writer, sheet_name=name, index=False)
        else:
            df.to_excel(file, sheet_name=name, index=False)


class GetResults(object):

    def __init__(
            self, get_defaults, params={}, urls=None, random_params={}, base_response=None, ajax_data=None,
            ajax_tab=None, tab_name='shop_id', ajax_children=None, params_ajax={}, urls_ajax=None,
            tab_shop=False, results_tree='results', response=None,
    ):
        self.ajax_data = ajax_data
        self.ajax_tab = ajax_tab
        self.tab_name = tab_name
        self.ajax_children = ajax_children
        self.get_defaults = get_defaults
        self.params = params
        self.urls = urls
        self.random_params = random_params
        self.urls_ajax = urls_ajax if urls_ajax else self.urls
        self.params_ajax = params_ajax
        self.results_tree = results_tree
        self.base_response = base_response
        self.tab_shop = tab_shop
        self.response = response


    def get_tree(self, resp_json_table, params, path, resp_json_children=None):

        if resp_json_children:
            click_obj = [str(x[0][0]) for x in zip(resp_json_table, resp_json_children) if x[0][1] != "total" and x[1]]
        else:
            click_obj = [str(x[0]) for x in resp_json_table if x[1] != "total"]
        choice_click = random.choice(click_obj)
        params_clicked = {
            "path": path + "_" + choice_click,
            "clicked_obj": choice_click,
            "parent": choice_click,
        }

        params_ajax = params.copy()
        params_ajax.update(params_clicked)

        response = self.get_response_report(params=params_ajax, urls=self.urls_ajax)

        return {"response": response, "path": params_clicked["path"]}

    def open_tree_ajax(self):

        resp_json_children = None
        if self.ajax_children:
            resp_json_children = self.ajax_children(self.response.json())

        params_ajax_curr = {
            'resp_json_table': self.base_response if self.base_response else self.ajax_data(self.response.json()),
            'resp_json_children': resp_json_children,
            'params': self.params,
            'path': 'i',
        }

        params_ajax_curr.update(self.params_ajax)

        resp_ajax = self.get_tree(**params_ajax_curr)

        while True:

            resp_ajax_json_table = resp_ajax['response'].json().get('df_to_dict')
            resp_ajax_json_children = resp_ajax['response'].json().get('children')

            if not resp_ajax_json_table or not any(resp_ajax_json_children):
                return resp_ajax['response']
            elif len(params_ajax_curr.get('path').split('_')) > 15:
                raise NameError('Big_recursions')
            else:
                params_ajax = params_ajax_curr.copy()
                params_ajax['path'] = resp_ajax.get('path')
                params_ajax['resp_json_table'] = resp_ajax_json_table
                params_ajax['resp_json_children'] = resp_ajax_json_children

                resp_ajax = self.get_tree(**params_ajax)


    def tab_shops(self):

        shop_ids = self.ajax_tab(self.response.json())
        params_shop = self.params.copy()
        params_shop[self.tab_name] = random.choice(shop_ids) if shop_ids else None
        return self.get_response_report(params=params_shop, urls=self.urls)

    def get_response_report(self, urls, params=None, method='post'):
        time_wait = time.clock()
        urls_requests = self.get_defaults['parent_url'] + urls
        data = json.dumps(params)
        logger.info({'url': urls_requests, 'params': params})

        req_params = {
            'url': urls_requests,
            'headers': self.get_defaults['headers'],
            'timeout': 120 * 2
        }
        if method == 'post' and params != None:
            req_params.update({'data': data})

        response = getattr(requests, method)(**req_params)

        result_params = {
            'time': datetime.datetime.now().strftime('%m-%d-%Y, %H:%M:%S'),
            'test_name': urls,
            'outcome': response.status_code,
            'error': response.status_code if response.status_code in [400, 500, 401, 403, 502] else '',
            'duration': time.clock() - time_wait,
            'user_name': self.get_defaults.get('response').get('username'),
            'random': self.random_params.get('random'),
            'params': params,
            'urls_requests': urls_requests,
            'params_url': base64.b64encode(urllib.parse.quote(data).encode()).decode().strip('=')
        }

        GenerateFiles().results_to_excel(result=result_params,
                                         name=self.urls.split('/')[-2] if self.urls else urls.split('/')[-2])
        return response

    @staticmethod
    def get_drill_down(get_defaults, urls, params, dt, path=None):

        params_category_delta = params.copy()
        params_category_delta.update({
            'month': dt,
            'view_type': 'get_category_delta',
            'period': dt,
            'cat_id': -1,
            'parent': -1,
            'number': 0,

        })

        params_month = params.copy()
        params_month.update({
            'month': dt,
            'view_type': "get_new_charts" if path else 'get_month'
        })

        if path:
            cat_id = path[-1]
            parent = path[0]
            params_category_delta.update(
                {
                    'cat_id': cat_id,
                    'parent': parent,
                    'number': len(path),
                    'path': path,
                }
            )
            params_month.update(
                {
                    'cat_id': cat_id,
                    'parent': parent,
                    'path': path,
                }
            )

        result = {
            "time": datetime.datetime.now().strftime("%m-%d-%Y, %H:%M:%S"),
            "test_name": "drill_down",
            "user_name": get_defaults.get("response").get("username"),
            'params': params_category_delta,

        }
        time_wait_cat = time.clock()

        get_category_delta = requests.post(get_defaults['parent_url'] + urls, data=json.dumps(params_category_delta),
                                           headers=get_defaults['headers'], timeout=120 * 2)

        result.update(
            {'params': params_category_delta,
             'duration': time.clock() - time_wait_cat,
             "outcome": get_category_delta.status_code,
             'error': get_category_delta.status_code if get_category_delta.status_code in [400, 500, 401, 403,
                                                                                           502] else '',
             },
        )
        GenerateFiles().results_to_excel(result, name="drill_down")
        time_wait_charts = time.clock()
        get_month = requests.post(get_defaults['parent_url'] + urls,
                                  data=json.dumps(params_month), headers=get_defaults['headers'], timeout=120 * 2)

        result.update(
            {'params': params_month,
             'duration': time.clock() - time_wait_charts,
             "outcome": get_category_delta.status_code,
             'error': get_month.status_code if get_month.status_code in [400, 500, 401, 403, 502] else '',
             },
        )
        GenerateFiles().results_to_excel(result, name=urls.split('/')[-2])
        return {
            'get_category_delta': get_category_delta,
            'get_month': get_month,
            'path': path
        }

    def results_ajax(self):

        self.response = self.get_response_report(params=self.params, urls=self.urls)
        results = []

        if self.response.json().get(self.results_tree) and self.tab_shop:
            results = self.tab_shops()

        if self.response.json().get(self.results_tree) and self.random_params.get('tree_ajax'):
            results = self.open_tree_ajax()

        return results if results else self.response
