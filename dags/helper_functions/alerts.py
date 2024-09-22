from airflow.providers.slack.hooks.slack_webhook import SlackWebhookHook
from airflow.hooks.base_hook import BaseHook
from urllib.parse import quote

def send_slack_alert(context):

    base_url = "https://airflow.kevinesg.com"
    
    # Retrieve task instance and DAG run information
    ti = context['task_instance']
    dag_run_id = context['dag_run'].run_id
    base_date = context['execution_date'].isoformat()

    # Construct the log URL for the specific task
    log_url = f"{base_url}/dags/{ti.dag_id}/grid?base_date={base_date}&tab=logs&dag_run_id={quote(dag_run_id)}&task_id={quote(ti.task_id)}"
    print(f'log_url: {log_url}')
    # Prepare the blocks for Slack's Block Kit
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":red_circle: Task Failed",
                "emoji": True
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Task*: {ti.task_id}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Dag*: {ti.dag_id}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Execution Time*: {context.get('execution_date')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Log Url*: <{log_url}|View Logs>"
                }
            ]
        },
        {
            "type": "divider"
        }
    ]

    # Collect all failed tasks from the current DAG run
    failed_tasks = []
    for task_instance in context['dag_run'].get_task_instances():
        if task_instance.state == 'failed':
            failed_tasks.append(task_instance.task_id)

    if failed_tasks:
        # Add a section for failed tasks
        tasks_list = "\n".join(f"- {task}" for task in failed_tasks)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Failed Tasks:*\n{tasks_list}"
            }
        })

    # Sending the message using SlackWebhookHook
    hook = SlackWebhookHook(slack_webhook_conn_id='slack_webhook')
    hook.send(blocks=blocks)