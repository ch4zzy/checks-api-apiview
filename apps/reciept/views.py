from django.http import FileResponse
from django.shortcuts import redirect
from django.utils.text import slugify
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .constants import StatusType
from .models import Check, Printer
from .serializers import CheckSerializer, CheckUpdateSerializer, PrinterSerializer
from .tasks import async_create_pdf
from .validators import validate_order, validate_printers_by_point


class PrinterListAPIView(APIView):
    """
    List and create printer instances.
    """

    serializer_class = PrinterSerializer

    def get(self, request):
        printers = Printer.objects.all()
        serializer = self.serializer_class(printers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PrinterDetailAPIView(APIView):
    """
    CRUD operations for the printer instance.
    """

    serializer_class = PrinterSerializer

    def get_object(self, pk):
        try:
            return Printer.objects.get(pk=pk)
        except Printer.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self, request, pk):
        printer = self.get_object(pk)
        serializer = self.serializer_class(printer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        printer = self.get_object(pk)
        serializer = self.serializer_class(printer, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        printer = self.get_object(pk)
        printer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckListAPIView(APIView):
    """
    List and create check instances.
    """

    serializer_class = CheckSerializer

    def get(self, request):
        checks = Check.objects.all()
        serializer = self.serializer_class(checks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckDetailAPIView(APIView):
    """
    RUD operations for the check instance.
    """

    serializer_class = CheckSerializer

    def get_object(self, pk):
        try:
            return Check.objects.get(pk=pk)
        except Check.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get(self, request, pk):
        check = self.get_object(pk)
        serializer = self.serializer_class(check)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        check = self.get_object(pk)
        serializer = self.serializer_class(check, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        check = self.get_object(pk)
        check.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CheckCreateAPIView(APIView):
    """
    Create a new check instance and send it to the printers.
    """

    serializer_class = CheckSerializer

    def post(self, request):
        data = request.data

        point_id = data.get("point_id")
        order_id = data.get("order", {}).get("order_id")
        validate_printers_by_point(point_id)
        validate_order(order_id)

        printers = Printer.objects.filter(point_id=point_id)
        created_checks = []

        for printer in printers:
            data = {
                "printer": printer.id,
                "check_type": printer.check_type,
                "order": data["order"],
                "status": data.get("status", StatusType.NEW),
            }

            serializer = self.serializer_class(data=data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            check = serializer.save()
            created_checks.append(serializer.data)
            async_create_pdf.delay(check.id, printer.check_type, data["order"])
        return Response(created_checks, status=status.HTTP_201_CREATED)


class CheckRetrieveUpdateAPIView(APIView):
    """
    Retrieve or Update the check instance, returns a file and marks the check as printed if updated.
    """

    serializer_class = CheckUpdateSerializer

    def get_object(self, pk):
        """
        Get the check object based on the provided 'pk'.
        """
        try:
            return Check.objects.get(pk=pk)
        except Check.DoesNotExist:
            raise status.HTTP_404_NOT_FOUND

    def get_pdf_file_response(self, instance):
        """
        Get the PDF file response of the check instance.
        """
        file_name = instance.pdf_file.name
        response = FileResponse(instance.pdf_file, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={slugify(file_name)}"
        return response

    def perform_update(self, instance):
        """
        Update the check instance and set the status to 'StatusType.PRINTED'.
        """
        instance.status = StatusType.PRINTED
        instance.save()

    def get(self, request, pk, format=None):
        """
        Retrieve the check instance and return the PDF file.
        """
        instance = self.get_object(pk)
        self.serializer_class(instance)
        return self.get_pdf_file_response(instance)

    def put(self, request, pk, format=None):
        """
        Update the check instance and return the PDF file.
        """
        instance = self.get_object(pk)
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            self.perform_update(instance)
            return redirect("reciept:check-update-retrieve", pk=instance.id)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
