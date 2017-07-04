from __future__ import absolute_import

import airflow
from airflow.operators import python_operator
import datetime
import json
import numpy
import os
import pandas
import scipy.stats
import sys
import unittest

# since we're sitting in a subdirectory...
fairflow_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if not fairflow_dir in sys.path:
    sys.path.append(fairflow_dir)
import fairflow



class Dataset(fairflow.FOperator):    
    def run(self, **context):
        # generate data
        x = numpy.arange(10).astype(float)
        y = x**2 + numpy.random.uniform(size=10)
        data = {
            "x": list(x),
            "y": list(y)
        }
        return json.dumps(data)

    def call(self, dag):
        t = python_operator.PythonOperator(
            task_id=self.id,
            python_callable=self.run,
            dag=dag
        )
        return t


class LinearModel(fairflow.FOperator):
    def run(self, **context):
        # get data
        data_str = fairflow.utils.get_param("data", context)
        data = json.loads(data_str)
        x = data["x"]
        y = data["y"]
        # make a linear fit
        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, y)
        # return R²
        return json.dumps(float(r_value))

    def call(self, dag):
        t_data = Dataset()(dag)
        t = python_operator.PythonOperator(
            task_id=self.id,
            python_callable=self.run,
            provide_context=True,
            templates_dict={
                "data" : fairflow.utils.xcom_result(t_data)
            },
            dag=dag
        )
        t.set_upstream(t_data)
        return t


class PolynomialModel(fairflow.FOperator):
    def __init__(self, degree, id=None):
        self.degree = degree
        return super().__init__(id)

    def run(self, **context):
        # get data
        data_str = fairflow.utils.get_param("data", context)
        data = json.loads(data_str)
        x = data["x"]
        y = data["y"]
        # make a polyfit (ref: https://stackoverflow.com/questions/893657/how-do-i-calculate-r-squared-using-python-and-numpy)
        coeffs = numpy.polyfit(x, y, self.degree)
        p = numpy.poly1d(coeffs)
        yhat = p(x)                         # or [p(z) for z in x]
        ybar = numpy.sum(y)/len(y)          # or sum(y)/len(y)
        ssreg = numpy.sum((yhat-ybar)**2)   # or sum([ (yihat - ybar)**2 for yihat in yhat])
        sstot = numpy.sum((y - ybar)**2)    # or sum([ (yi - ybar)**2 for yi in y])
        r_squared = ssreg / sstot
        # return R²
        return json.dumps(float(r_squared))

    def call(self, dag):
        t_data = Dataset()(dag)
        t = python_operator.PythonOperator(
            task_id=self.id,
            python_callable=self.run,
            provide_context=True,
            templates_dict={
                "data" : fairflow.utils.xcom_result(t_data)
            },
            dag=dag
        )
        t.set_upstream(t_data)
        return t


class Compare(fairflow.FOperator):
    """A task that compare the LinearModel with the PolynomialModel. Returns: pandas.DataFrame"""
    def __init__(self, fops_models, id=None):
        self.fops_models = fops_models
        return super().__init__(id)

    @staticmethod
    def compare(**context):
        """Accumulates the results of upstream tasks into a DataFrame"""
        task_ids = fairflow.utils.get_param("model_taskids", context)				# get the task ids of the upstream tasks
        comparison = pandas.DataFrame(columns=["modelname", "result"])
        for task_id in task_ids:
            modelresult = context["ti"].xcom_pull(task_id)					# pull the return value of the upstream task
            comparison.loc[-1] = task_id, modelresult
        return comparison

    def call(self, dag):
        """Instantiate upstream tasks, this task and set dependencies. Returns: task"""
        model_tasks = [					# instantiate tasks for running the different models
            f(dag)                      # by calling their FOperators on the current `dag`
            for f in self.fops_models	# notice that we do not know about the models upstream dependencies!
        ]
        t = python_operator.PythonOperator(
            task_id=self.__class__.__name__,
            python_callable=self.compare,
            provide_context=True,
            templates_dict={
                "model_taskids": [mt.task_id for mt in model_tasks]
            },
            dag=dag
        )
        t.set_upstream(model_tasks)
        return t


default_args = {
    'owner': 'fairflow.tests',
    'depends_on_past': False,
    'start_date': datetime.datetime(2017, 7, 1),
    'retries': 0,
    'max_active_runs': 1
}

# compare models
f_linear = LinearModel()
f_poly = PolynomialModel(degree=3)
f_compare = Compare([f_linear, f_poly])

# instantiate the dag
dag = airflow.DAG('example_models',
    default_args=default_args,
    schedule_interval=None
)
f_compare(dag)
