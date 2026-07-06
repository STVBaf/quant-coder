from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from market.services import get_or_create_stock

from .models import WatchItem


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    if not username or not password:
        return Response({"error": "用户名和密码必填"}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"error": "用户名已存在"}, status=400)

    user = User.objects.create_user(username=username, password=password)
    token = Token.objects.create(user=user)
    return Response({"token": token.key, "username": user.username})


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")
    user = authenticate(username=username, password=password)
    if not user:
        return Response({"error": "用户名或密码错误"}, status=400)

    token, _ = Token.objects.get_or_create(user=user)
    return Response({"token": token.key, "username": user.username})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({"username": request.user.username})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def watchlist(request):
    """List the user's watchlist, or add a stock to it."""
    if request.method == "POST":
        code = request.data.get("code", "").strip()
        if not code:
            return Response({"error": "缺少股票代码"}, status=400)
        stock = get_or_create_stock(code)
        WatchItem.objects.get_or_create(user=request.user, stock=stock)

    items = request.user.watchlist.select_related("stock")
    return Response(
        [{"code": i.stock.code, "name": i.stock.name} for i in items]
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def watch_remove(request, code):
    WatchItem.objects.filter(user=request.user, stock__code=code).delete()
    return Response(status=204)
