from django.urls import path

from app import views

urlpatterns = [
    path("health/", views.HealthView.as_view(), name="health"),
    path("documents/", views.DocumentListCreateView.as_view(), name="document-list-create"),
    path("documents/<int:pk>/", views.DocumentDetailView.as_view(), name="document-detail"),
    path(
        "documents/<int:pk>/chunks/<int:chunk_index>/context/",
        views.DocumentChunkContextView.as_view(),
        name="document-chunk-context",
    ),
    path("search/", views.SearchView.as_view(), name="search"),
]
