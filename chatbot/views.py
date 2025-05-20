from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .services.openai_service import ask_openai

@csrf_exempt
def chat_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        prompt = data.get("prompt", "")
        response = ask_openai(prompt)
        return JsonResponse({"response": response})
    return JsonResponse({"error": "Method not allowed"}, status=405)
