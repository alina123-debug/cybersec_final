from rest_framework import serializers
from .models import Alert, Case, Task, Rule, Dispatch
from core.models import Client, Employee

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "title", "done"]

class CaseSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = [
            "id","created_at","updated_at","client","severity","incident_type",
            "status","verdict","title","description","analyst_name","analyst_group",
            "source_ip","host_ip","hostname","evidence","tasks",
        ]

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = ["id","created_at","client","severity","incident_type","title","raw_event","is_false_positive"]

class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ["id","name","incident_type","severity","query_template","response_steps","enabled"]

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id","name","sla_critical_min","sla_high_min","sla_medium_min","sla_low_min"]

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ["id","client","full_name","email","telegram_handle","role"]
