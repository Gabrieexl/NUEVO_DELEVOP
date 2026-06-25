from rest_framework import serializers
from .models import Acta


class ActaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Acta
        fields = '__all__'
        read_only_fields = ('id', 'creadoEn', 'actualizadoEn', 'creadoPor')
