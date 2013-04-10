"""Root URL routing"""
from django.conf.urls.defaults import patterns
from django.conf.urls.static import static
from django.views.generic import TemplateView

from kitchen.dashboard import api
import kitchen.settings as settings


urlpatterns = patterns('',
    (r'^$', 'kitchen.dashboard.views.main'),
    (r'^virt/$', 'kitchen.dashboard.views.virt'),
    (r'^graph/$', 'kitchen.dashboard.views.graph'),
    (r'^plugins/((?P<plugin_type>(virt|v|list|l))/)?(?P<name>[\w\-\_]+)/(?P<method>\w+)/?$', 'kitchen.dashboard.views.plugins'),
    (r'^api/nodes/(?P<name>\w+)$', api.get_node),
    (r'^api/nodes', api.get_nodes),
    (r'^api/roles', api.get_roles),
    (r'^404', TemplateView.as_view(template_name="404.html")),
)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
