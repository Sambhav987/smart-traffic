from django.shortcuts import render
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from .traffic_system import VideoCamera, traffic_state, intersection_id, intersection_name
from .models import Congestion, Accident, HistoricData, PushToken
from core.services.push import send_push
import json
from django.views.decorators.http import require_POST

def index(request):
    congestions = Congestion.objects.all().order_by('-id')
    accidents = Accident.objects.all().order_by('-id')
    historic_data = HistoricData.objects.all().order_by('-id')
    return render(request, 'core/index.html', {
        'congestions': congestions,
        'accidents': accidents,
        'historic_data': historic_data,
    })

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            break

def video_feed(request, section):
    # Initializes camera based on current traffic_state source for this section
    return StreamingHttpResponse(gen(VideoCamera(section)),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

@csrf_exempt
def upload_video(request, section):
    if request.method == 'POST' and request.FILES.get('video_file'):
        video_file = request.FILES['video_file']
        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'videos'))
        filename = fs.save(video_file.name, video_file)
        file_path = fs.path(filename)
        
        # Update traffic state with new source
        traffic_state.set_video_source(section, file_path)
        
        return JsonResponse({'status': 'success', 'file_path': file_path})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def switch_live(request, section):
    if request.method == 'POST':
        # 0 is the default index for the first webcam
        traffic_state.set_video_source(section, 0)
        return JsonResponse({'status': 'success', 'message': f'Switched {section} to live camera'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
def stop_feed(request, section):
    if request.method == 'POST':
        traffic_state.set_video_source(section, None)
        return JsonResponse({'status': 'success', 'message': f'Stopped feed for {section}'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@csrf_exempt
@require_POST
def notify_emergency(request, section):
    try:
        send_push(
            title="Emergency vehicle approaching",
            body=f"Emergency vehicle reported at {section}",
            data={
                "intersectionId": intersection_id,
                "intersectionName": intersection_name,
                "section": section,
                "type": "emergency",
            },
        )
        return JsonResponse({'status': 'success', 'message': f'Emergency notification sent for {section}'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_POST
def register_push_token(request):
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "invalid json"}, status=400)

    token = body.get("token")
    if not token:
        return JsonResponse({"error": "token required"}, status=400)

    PushToken.objects.update_or_create(
        token=token,
        defaults={"platform": body.get("platform", "")},
    )
    return JsonResponse({"ok": True})
