#MIT License

#Copyright (c) 2017 Zymergen, Inc.

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import abc
from airflow.operators import BaseOperator


class FOperator(object):
    """Abstract wrapper around tasks."""
    __metaclass__ = abc.ABCMeta
    __instances__ = {}      # dagid.taskid : Operator

    def __init__(self, id=None):
        self.id = self.__class__.__name__ if id is None else id
        return

    def __call__(self, dag):
        """Get a unique instance of the task in the dag.
        
        Parameters:
            dag (airflow.models.DAG) : The DAG that this task will be a member of.

        Returns:
            t (airflow.operator.BaseOperator) : The Task described by this FOperator.
        """
        key = "{}.{}".format(dag.dag_id, self.id)   # the dagid can be different
        if not key in FOperator.__instances__:
            task = self.call(dag)
            assert task != None, "Calling '{}' returned 'None' where a 'BaseOperator' instance was expected.".format(self.id)
            assert isinstance(task, BaseOperator), "Calling '{}' did not return a BaseOperator instance (but a '{}' instead).".format(self.id, task.__class__.__name__)
            assert task.task_id == self.id, "task_id '{}' must be identical to the FOperator.id '{}'".format(task.task_id, self.id)
            FOperator.__instances__[key] = task     # store the task instance
        return FOperator.__instances__[key]
    
    @abc.abstractclassmethod
    def call(self, dag):
        """Creates an instance of the Task."""
        raise NotImplementedError("The 'call' method of the '{}' FOperator was not implemented. Shame on you.".format(self.id))
        return

