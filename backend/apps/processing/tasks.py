from config.celery import app
from .services import DataProcessingService
from .models import ProcessingTask


@app.task(bind=True, max_retries=0)
def execute_processing_task(self, task_id: int):
    """Celery 异步执行数据处理任务"""
    task = ProcessingTask.objects.get(id=task_id)
    task.celery_task_id = self.request.id
    task.save(update_fields=['celery_task_id'])
    DataProcessingService.execute_task(task)
