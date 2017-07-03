from __future__ import absolute_import

import airflow
from airflow.operators import python_operator
import datetime
import json
import numpy
import os
import sys
import unittest

# since we're sitting in a subdirectory...
fairflow_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if not fairflow_dir in sys.path:
    sys.path.append(fairflow_dir)
import fairflow



class IntegerTask(fairflow.FOperator):
    def __init__(self, value):
        self.value = value
        return super().__init__(id="IntTask_v{}".format(value))
    
    def run(self, **context):
        return json.dumps(self.value)

    def call(self, dag):
        t = python_operator.PythonOperator(
            task_id=self.id,
            python_callable=self.run,
            dag=dag
        )
        return t


class SumTask(fairflow.FOperator):
    def __init__(self, fops_upstream, id=None):
        self.fops_upstream = fops_upstream
        return super().__init__(id=id)
    
    def run(self, **context):
        # get all upstream results
        results = [
            json.loads(fairflow.utils.get_param(fop.id, context))
            for fop in self.fops_upstream
        ]
        return json.dumps(float(numpy.sum(results)))

    def call(self, dag):
        tasks_upstream = [fop(dag) for fop in self.fops_upstream]       # instantiate all upstream tasks
        t_sum = python_operator.PythonOperator(
            task_id=self.id,
            python_callable=self.run,
            provide_context=True,
            templates_dict={
                ut.task_id : fairflow.utils.xcom_result(ut)
                for ut in tasks_upstream
            },
            dag=dag
        )
        t_sum.set_upstream(tasks_upstream)
        return t_sum


class TaskTest(fairflow.FOperator):
    """Only suceeds if the return value of the upstream task matches the expected result."""
    def __init__(self, f_task, expected_result, id = None):
        self.f_task = f_task
        self.expected_result = expected_result
        return super().__init__(id)

    def run(self, **context):
        result_str = fairflow.utils.get_param("result", context)
        print("DEBUG: '{}'".format(result_str))
        result = json.loads(result_str) if result_str != 'None' else None
        is_match = result == self.expected_result
        if not is_match:
            raise ValueError("Task '{}' returned '{}' but '{}' was expected.".format(self.f_task.id, result, self.expected_result))
        return

    def call(self, dag):
        t_up = self.f_task(dag)
        t = python_operator.PythonOperator(
            task_id=self.id,
            python_callable=self.run,
            provide_context=True,
            templates_dict={
                "result": fairflow.utils.xcom_result(t_up)
            },
            dag=dag
        )
        t.set_upstream(t_up)
        return t


default_args = {
    'owner': 'fairflow.tests',
    'depends_on_past': False,
    'start_date': datetime.datetime(2017, 7, 1),
    'retries': 0,
    'max_active_runs': 1
}

# some upstream tasks that are shared across all tests
f1 = IntegerTask(1)
f2 = IntegerTask(2)
f3 = IntegerTask(3)

# testing the function of merge-layers
f_merge = fairflow.foperators.Merge([f1,f2,f3], "123-all")
f_merge_val = TaskTest(f_merge, None, "123-all-validation")

f_mergeresults = fairflow.foperators.MergeResults([f1,f2,f3], "123-list")
f_mergeresults_val = TaskTest(f_mergeresults, [1,2,3], "123-list-validation")

# testing the Sum-layer implemented above
f_sum = SumTask([f1,f2,f3], "123-sum")
f_sum_val = TaskTest(f_sum, 6, "123-sum-validation")


# now merge all individual tests with a Merge operation
f_all_done = fairflow.foperators.Merge([f_merge_val, f_mergeresults_val, f_sum_val], id="AllDone")


# instantiate the dag
dag = airflow.DAG('test_fairflow',
    default_args=default_args,
    schedule_interval=None
)
f_all_done(dag)
