from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Document


@login_required
def document_list(request):
    """List all documents from S3."""
    documents = Document.objects.all().order_by('-uploaded_at')
    
    return render(request, 'documents/document_list.html', {
        'documents': documents,
    })


@login_required
def document_detail(request, doc_id):
    """View document details."""
    document = get_object_or_404(Document, id=doc_id)
    
    return render(request, 'documents/document_detail.html', {
        'document': document,
    })


@login_required
def document_view(request, doc_id):
    """View/download document from S3."""
    document = get_object_or_404(Document, id=doc_id)
    
    try:
        # Get the file URL (S3 or local)
        file_url = document.file.url
        return redirect(file_url)
    except Exception as e:
        messages.error(request, f'Error accessing file: {str(e)}')
        return redirect('documents:document_list')
