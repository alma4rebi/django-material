"""
Simple module system
"""
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.utils.functional import curry

from .registry import default_registry
from .urlconf import ModuleURLResolver


class Module(object):
    """
    Base class for website modules
    """
    order = 10
    icon = "mdi-action-receipt"

    def __init__(self, register_to=None, app_name=None):
        self.app_name = app_name or self.slug
        if register_to is None:
            register_to = default_registry
        register_to.register(self)

    @property
    def app_label(self):
        module_path = self.__class__.__module__.split('.')
        try:
            module_path.remove('modules')
        except ValueError:
            pass

        return module_path[-1].lower()

    @property
    def slug(self):
        return self.__class__.__name__.rsplit('.')[-1].lower()

    @property
    def label(self):
        return self.slug.title()

    def description(self):
        return (self.__doc__ or "").strip()

    def ready(self):
        pass

    def has_perm(self, user):
        return True

    def user_module(self, user):
        class Proxy(self.__class__):
            def __getattribute__(proxy_self, name):
                if name == 'user':
                    return user

                cls_attr = getattr(self.__class__, name, None)
                if callable(cls_attr):
                    return curry(cls_attr, proxy_self)

                return getattr(self, name)

            def __eq__(proxy_self, other):
                return self == other

        return Proxy()

    def menu(self):
        try:
            return get_template('{}/menu.html'.format(self.app_label))
        except TemplateDoesNotExist:
            return None

    def get_urls(self):
        from django.views import generic
        return [url('^$', generic.TemplateView.as_view(
            template_name="{}/index.html".format(self.app_label)), name="index")]

    def index_url(self):
        return reverse('{}:index'.format(self.slug), current_app=self.app_name)

    @property
    def urls(self):
        base_url = '^{}/'.format(self.slug)
        return ModuleURLResolver(base_url, self.get_urls(), module=self, app_name=self.app_name, namespace=self.slug)


class InstallableModule(Module):
    @property
    def installed(self):
        from .models import Module as DbModule
        return DbModule.objects.installed(self.slug)
