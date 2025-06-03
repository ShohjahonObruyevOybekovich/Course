from rest_framework import serializers

from .models import File, Contract


class FileUploadSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = [
            'id',
            'file',
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get("request")
        representation["file"] = request.build_absolute_uri(instance.file.url)
        return representation
