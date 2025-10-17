from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404
from django.urls.conf import include

admin.site.site_header = "VogueVue Admin"
admin.site.site_title = "VogueVue Admin Portal"
admin.site.index_title = "Welcome To VogueVue"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('voguevue.urls')),
    path('volt/', include('admin_volt.urls')),
]

handler404 = 'voguevue.views.error_404'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
 