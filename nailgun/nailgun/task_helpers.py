from celery.task import task, chord, TaskSet
from functools import wraps


# Example: graph = {1: [4], 2: [], 3: [2,6], 4:[2,3], 5: [], 6: [2]}
# 1 depends on 4, 3 depends on 2 and 6, etc.
def topol_sort(graph):
    # NOTE(mihgen): Installation components dependency resolution
    # From nodes.roles.recipes we know recipes that needs to be applied
    # We have to apply them in an order according to specified dependencies
    # To sort in an order, we use DFS(Depth First Traversal) over DAG graph
    # Exception is raised if there is a cycle
    def dfs(v):
        color[v] = "gray"
        for w in graph[v]:
            if color[w] == "black":
                continue
            elif color[w] == "gray":
                raise TaskError(deploy_cluster.request.id,
                        "Graph contains cycles, processed %s depends on %s" \
                                % (v, w), cluster_id=cluster_id)
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
