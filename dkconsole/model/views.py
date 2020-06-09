from django.shortcuts import render
from .services import MLModelService
from .serializers import MLModelSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view

# Create your views here.


@api_view(['GET'])
def index(request):
    models = MLModelService.get_mlmodels()

    serializer = MLModelSerializer(models, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def delete(request):
    try:
        model_path = request.data['model_path']

        MLModelService.delete_model(model_path)

        return Response({"success": True})
    except Exception as e:
        print(e)
        return Response({"success": False})


@api_view(['POST'])
def update_meta(request, model_name):
    try:
        update_parms = request.data['update_parms']

        MLModelService.update_meta(model_name, update_parms)

        return Response({"success": True})
    except Exception as e:
        print(e)
        return Response({"success": False})
