from __future__ import absolute_import

from airflow.operators import dummy_operator
from airflow.operators import python_operator
import json

from . import core
from . import utils


class Merge(core.FOperator):
    """A dummy task that depends on the success of upstream tasks."""
    def __init__(self, fops, id):
        self.fops = fops
        return super().__init__(id)

    def call(self, dag):
        tasks = [fop(dag) for fop in self.fops]
        t = dummy_operator.DummyOperator(task_id=self.id, dag=dag)
        t.set_upstream(tasks)
        return t


class MergeResults(core.FOperator):
    """A dummy task that concatenates (json dumpsed) upstream results into a single list (json dumpsed)."""
    def __init__(self, fops, id):
        self.fops = fops
        return super().__init__(id)

    def run(self, **context):
        results_str = [utils.get_param(fop.id, context) for fop in self.fops]
        results = [json.loads(r) if r != 'None' else None for r in results_str]
        return json.dumps(results)

    def call(self, dag):
        tasks = [fop(dag) for fop in self.fops]
        t = python_operator.PythonOperator(
            task_id=self.id,
            python_callable=self.run,
            provide_context=True,
            templates_dict={
                ut.task_id : utils.xcom_result(ut)
                for ut in tasks
            },
            dag=dag
        )
        t.set_upstream(tasks)
        return t
