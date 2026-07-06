from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Conversation, Message, ResearchTask
from .research.task_runner import start_task
from .service import run_agent


@api_view(["POST"])
def chat(request):
    """One chat turn. Body: {conversation_id?, message}.

    Replays prior turns as context, runs the tool-use loop, persists both turns.
    Anonymous users get an ephemeral conversation (not tied to a user).
    """
    if not settings.ANTHROPIC_API_KEY:
        return Response({"error": "Agent 未配置 API key，请在 backend/.env 填写"}, status=503)

    text = (request.data.get("message") or "").strip()
    if not text:
        return Response({"error": "消息不能为空"}, status=400)

    convo = _get_or_create_conversation(request)
    history = [{"role": m.role, "content": m.text} for m in convo.messages.all()]
    history.append({"role": "user", "content": text})

    result = run_agent(history)

    Message.objects.create(conversation=convo, role="user", text=text)
    Message.objects.create(
        conversation=convo,
        role="assistant",
        text=result["reply"],
        trace=result["trace"],
    )

    return Response(
        {
            "conversation_id": convo.id,
            "reply": result["reply"],
            "trace": result["trace"],
        }
    )


def _get_or_create_conversation(request) -> Conversation:
    convo_id = request.data.get("conversation_id")
    user = request.user if request.user.is_authenticated else None
    if convo_id:
        try:
            return Conversation.objects.get(id=convo_id)
        except Conversation.DoesNotExist:
            pass
    return Conversation.objects.create(user=user)


@api_view(["POST"])
def research_create(request):
    """Start an autonomous research task. Body: {prompt, codes: [..]}.

    Runs the Claude Agent SDK loop in a background thread; poll research_detail
    for progress. Anonymous allowed (task not tied to a user).
    """
    if not settings.ANTHROPIC_API_KEY:
        return Response({"error": "Agent 未配置 API key，请在 backend/.env 填写"}, status=503)

    prompt = (request.data.get("prompt") or "").strip()
    codes = request.data.get("codes") or []
    if not prompt:
        return Response({"error": "研究目标不能为空"}, status=400)
    if not isinstance(codes, list) or not codes:
        return Response({"error": "请至少提供一个股票代码"}, status=400)

    task = ResearchTask.objects.create(
        user=request.user if request.user.is_authenticated else None,
        prompt=prompt,
        codes=[str(c).strip() for c in codes],
    )
    start_task(task.id)
    return Response({"id": task.id, "status": task.status}, status=201)


@api_view(["GET"])
def research_detail(request, task_id):
    """Task status + ordered iteration timeline, for polling."""
    try:
        task = ResearchTask.objects.get(id=task_id)
    except ResearchTask.DoesNotExist:
        return Response({"error": "任务不存在"}, status=404)

    return Response(
        {
            "id": task.id,
            "prompt": task.prompt,
            "codes": task.codes,
            "status": task.status,
            "report": task.report,
            "error": task.error,
            "iterations": [
                {"seq": it.seq, "kind": it.kind, "payload": it.payload}
                for it in task.iterations.all()
            ],
        }
    )
