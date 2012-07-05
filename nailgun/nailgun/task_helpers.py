import logging
from functools import wraps

from celery.task import task, chord, TaskSet
from nailgun.models import Cluster, Node

logger = logging.getLogger(__name__)


class TaskError(Exception):

    def __init__(self, task_id, error, cluster_id=None, node_id=None):
        self.message = ""
        node_msg = ""
        cluster_msg = ""

        if node_id:
            node_msg = ", node_id='%s'" % (node_id)
        if cluster_id:
            cluster_msg = ", cluster_id='%s'" % (cluster_id)

        self.message = "Error in task='%s'%s%s. Error message: '%s'" % (
                    task_id, cluster_msg, node_msg, error)

        try:
            Exception.__init__(self, self.message)
            logger.error(self.message)
            if node_id:
                node = Node.objects.get(id=node_id)
                node.status = "error"
                node.save()

            if cluster_id:
                cluster = Cluster.objects.get(id=cluster_id)
                cluster.last_task = cluster.current_task
                cluster.current_task = None
                cluster.save()
        except:
            logger.exception("Exception in exception handler occured")

    def __str__(self):
        return repr(self.message)


def topol_sort(graph):
    """ Depth First Traversal algorithm for sorting DAG graph.

    Example graph: 1 depends on 4; 3 depends on 2 and 6; etc.
    Example code:

    .. code-block:: python

        >>> graph = {1: [4], 2: [], 3: [2,6], 4:[2,3], 5: [], 6: [2]}
        >>> topol_sort(graph)
        [2, 6, 3, 4, 1, 5]

    Exception is raised if there is a cycle:

    .. code-block:: python

        >>> graph = {1: [4], 2: [], 3: [2,6], 4:[2,3,1], 5: [], 6: [2]}
        >>> topol_sort(graph)
        ...
        Exception: Graph contains cycles, processed 4 depends on 1

    """

    def dfs(v):
        color[v] = "gray"
        for w in graph[v]:
            if color[w] == "black":
                continue
            elif color[w] == "gray":
                raise Exception(
                        "Graph contains cycles, processed %s depends on %s" % \
                                (v, w))
            dfs(w)
        color[v] = "black"
        _sorted.append(v)

    _sorted = []
    color = {}
    for j in graph:
        color[j] = "white"
    for i in graph:
        if color[i] == "white":
            dfs(i)

    return _sorted


# This code is inspired by
# https://github.com/NetAngels/celery-tasktree/blob/master/celery_tasktree.py
def task_with_callbacks(func, **options):
    """ decorator "task with callbacks"

    Callback or list of callbacks which go to function in "callbacks" kwarg,
    will be executed after the function, regardless of the subtask's return
    status.

    If subtask (function) result is an object, then a property named
    "async_result" will be added to that object so that it will be possible to
    join() for that result.
    """
    return task(run_with_callbacks(func), **options)


def run_with_callbacks(func):
    """Decorator "run with callbacks"

    Function is useful as decorator for :meth:`run` method of tasks which are
    subclasses of generic :class:`celery.task.Task` and are expected to be used
    with callbacks.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        callback = kwargs.pop('callback', None)
        retval = func(*args, **kwargs)
        if callback:
            retval = callback.apply_async()
        return retval
    return wrapper


class TaskPool(object):

    def __init__(self):
        self.pool = []

    def push_task(self, func, args=None, kwargs={}):
        task = {'func': func, 'args': args, 'kwargs': kwargs}
        # TODO(mihgen): check that list of func has correct args
        self.pool.append(task)

    @task_with_callbacks
    def _chord_task(taskset, clbk):
        # We have to create separate subtask that contains chord expression
        #   because otherwise chord functions get applied synchronously
        return chord([tsk['func'].subtask(args=tsk['args'], \
                    kwargs=tsk['kwargs']) for tsk in taskset])(clbk)

    def _get_head_task(self):
        prev_task = None
        for t in reversed(self.pool):
            if isinstance(t['func'], list):
                task = self._chord_task.subtask((t['func'], prev_task))
            else:
                kwargs = t['kwargs'] or {}
                if prev_task:
                    kwargs['callback'] = prev_task
                task = t['func'].subtask(args=t['args'], kwargs=kwargs)
            prev_task = task
        print "Returning head task: %s" % task
        return task

    def apply_async(self):
        # We need only head task. When it's execution is done,
        #   run_with_callbacks will call it's subtask
        async_result = self._get_head_task().apply_async()
        return async_result
