from django.contrib.auth.models import User
from django.db import models


class Conversation(models.Model):
    user = models.ForeignKey(
        User, related_name="conversations", null=True, blank=True, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Message(models.Model):
    ROLES = [("user", "user"), ("assistant", "assistant")]

    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    role = models.CharField(max_length=10, choices=ROLES)
    text = models.TextField()
    trace = models.JSONField(default=list)  # tool calls behind an assistant turn
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class ResearchTask(models.Model):
    """An autonomous research run: a natural-language goal over some stocks,
    driven by the Claude Agent SDK loop in a background thread."""

    STATUS = [
        ("pending", "pending"),
        ("running", "running"),
        ("done", "done"),
        ("failed", "failed"),
    ]
    user = models.ForeignKey(
        User, related_name="research_tasks", null=True, blank=True,
        on_delete=models.CASCADE,
    )
    prompt = models.TextField()
    codes = models.JSONField(default=list)  # ["600519", ...]
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    report = models.TextField(blank=True)   # agent's final conclusion
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class ResearchIteration(models.Model):
    """One event in a task's timeline: a thought, a tool call, or a code run
    with its backtest metrics. Kept flat so the UI can render a timeline."""

    task = models.ForeignKey(
        ResearchTask, related_name="iterations", on_delete=models.CASCADE
    )
    seq = models.PositiveIntegerField()          # order within the task
    kind = models.CharField(max_length=20)       # thought | tool_call | run_strategy | status
    payload = models.JSONField(default=dict)     # kind-specific data
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["seq"]
