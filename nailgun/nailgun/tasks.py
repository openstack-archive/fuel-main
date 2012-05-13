from celery.task import task

@task
def add(x, y):
  for i in xrange(1, 10):
    time.sleep(1)
    add.update_state(state="PROGRESS", meta={"current": i, "total": 10})
  return x + y

