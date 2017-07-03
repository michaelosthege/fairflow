from __future__ import absolute_import

import ast
import airflow.operators

def get_param(name, dictionary):
    """Retrieves the parameter dictionary[name] or dictionary["templates_dict"][name]
    
    Raises:
        KeyError
    """
    if ("templates_dict" in dictionary):
        dictionary = dictionary["templates_dict"]
    if (name in dictionary):
        return dictionary[name]
    raise KeyError("'{}' was not found in context.".format(name))

def xcom_result(task_or_id):
    """Returns a jinja template for xcom_pulling the return value of [task].
    
    Parameters:
        task (str or BaseOperator): the task for which to pull the result
    """
    if isinstance(task_or_id, str):
        return "{{ti.xcom_pull(task_ids='" + task_or_id + "')}}"
    elif isinstance(task_or_id, airflow.operators.BaseOperator):
        return "{{ti.xcom_pull(task_ids='" + task_or_id.task_id + "')}}"
    else:
        raise TypeError("Expected str or BaseOperator, but got {}".format(task_or_id.__class__.__name__))