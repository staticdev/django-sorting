from django.db import models
from django.db.models.related import RelatedObject
from django.forms.forms import pretty_name
from django.utils.encoding import force_str, force_text
from django.utils import six


def label_for_field(name, model, return_attr=False):
    """
    Returns a sensible label for a field name. The name can be a callable,
    property (but not created with @property decorator) or the name of an
    object's attribute, as well as a genuine fields. If return_attr is
    True, the resolved attribute (which could be a callable) is also returned.
    This will be None if (and only if) the name refers to a field.
    """
    attr = None
    try:
        field = model._meta.get_field_by_name(name)[0]
        if isinstance(field, RelatedObject):
            label = field.opts.verbose_name
        else:
            label = field.verbose_name
    except models.FieldDoesNotExist:
        if name == "__unicode__":
            label = force_text(model._meta.verbose_name)
            attr = six.text_type
        elif name == "__str__":
            label = force_str(model._meta.verbose_name)
            attr = bytes
        else:
            if callable(name):
                attr = name
            elif hasattr(model, name):
                attr = getattr(model, name)
            else:
                message = "Unable to lookup '%s' on %s" % (name, model._meta.object_name)
                raise AttributeError(message)

            if hasattr(attr, "short_description"):
                label = attr.short_description
            elif (isinstance(attr, property) and
                  hasattr(attr, "fget") and
                  hasattr(attr.fget, "short_description")):
                label = attr.fget.short_description
            elif callable(attr):
                if attr.__name__ == "<lambda>":
                    label = "--"
                else:
                    label = pretty_name(attr.__name__)
            else:
                label = pretty_name(name)
    if return_attr:
        return (label, attr)
    else:
        return label
