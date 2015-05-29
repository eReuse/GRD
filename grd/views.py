from rest_framework import status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView

from .models import Agent, Device, Event
from .serializers import (
    DeviceSerializer, EventSerializer, RecycleSerializer, RegisterSerializer
)


class DeviceView(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    # permission_classes = (IsAdminUser,)
    
    @detail_route(methods=['get'])
    def log(self, request, pk=None):
        device = self.get_object()
        queryset = Event.objects.related_to_device(device)
        serializer = EventSerializer(queryset, many=True,
                                     context={'request': request})
        return Response(serializer.data)
    
    @list_route(methods=['post'], permission_classes=[IsAuthenticated])
    def register(self, request):
        if not request.data:
            return Response({'invalid_request': 'empty POST request'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        serializer = RegisterSerializer(data=request.data,
                                        context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        
        # create devices and logs
        try:
            dev = Device.objects.get(id=data['device']['id'])
        except Device.DoesNotExist:
            dev = Device.objects.create(**data['device'])
        agent = request.user.agent
        log = dev.logs.create(event=Event.REGISTER, agent=agent,
                              event_time=data['event_time'],
                              by_user=data['by_user'])
        
        for component in data['components']:
            try:
                device = Device.objects.get(id=component['id'])
            except Device.DoesNotExist:
                log.components.create(**component)
            else:
                log.components.add(device)
        
        headers = {'Location': reverse('device-detail', args=[dev.pk],
                                       request=request)}
        return Response('{}', status=status.HTTP_201_CREATED, headers=headers)
    
    @detail_route(methods=['post'], permission_classes = [IsAuthenticated])
    def recycle(self, request, pk=None):
        if not request.data:
            return Response({'invalid_request': 'empty POST request'},
                            status=status.HTTP_400_BAD_REQUEST)
        
        dev = self.get_object()
        serializer = RecycleSerializer(data=request.data,
                                       context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        
        # create log
        agent = request.user.agent
        log = dev.logs.create(event=Event.RECYCLE, agent=agent,
                              event_time=data['event_time'],
                              by_user=data['by_user'])
        
        # Agent should explicity define which components are recycled
        for device in data['components']:
            log.components.add(device)
        
        headers = {'Location': 'foo'}
        # TODO(slamora): define log-detail view?
        # headers = {'Location': reverse('log-detail', args=[log.pk],
        #                                 request=request)}
        return Response('{}', status=status.HTTP_201_CREATED, headers=headers)
