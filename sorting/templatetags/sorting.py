from django import template

register = template.Library()

# TO-DO: receive a list and make a for in the template
@register.inclusion_tag('sorting/sort_link_frag.html', takes_context=True)
def sort_link(context, text, sort_field, visible_name=None):
    """Usage: {% sort_link "text" "field_name" %}
    Usage: {% sort_link "text" "field_name" "Visible name" %}
    """
    # general and outside FOR
    sorted_fields = False
    # specific to the field
    ascending = None
    # specific to the field
    class_attrib = 'sortable'
    # specific to the field
    orig_sort_field = sort_field
    if context.get('current_sort_field') == sort_field:
        sort_field = '-%s'%sort_field
        visible_name = '-%s'%(visible_name or orig_sort_field)
        sorted_fields = True
        ascending = False
        class_attrib += ' sorted descending'
    elif context.get('current_sort_field') == '-'+sort_field:
        visible_name = '%s'%(visible_name or orig_sort_field)
        sorted_fields = True
        ascending = True
        class_attrib += ' sorted ascending'

    if visible_name:
        if 'request' in context:
            request = context['request']
            request.session[visible_name] = sort_field
        
    if 'getsortvars' in context:
        extra_vars = context['getsortvars']
    else:
        if 'request' in context:
            request = context['request']
            getvars = request.GET.copy()
            if 'sort_by' in getvars:
                del getvars['sort_by']
            if len(getvars.keys()) > 0:
                context['getsortvars'] = "&%s" % getvars.urlencode()
            else:
                context['getsortvars'] = ''
            extra_vars = context['getsortvars']
            
        else:
            extra_vars = ''

        
    return {'text':text, 'sort_field':sort_field, 'extra_vars':extra_vars,
            'ascending':ascending, 'sorted_fields':sorted_fields, 'visible_name':visible_name, 'class_attrib': class_attrib
            }
    

@register.tag
def auto_sort(parser, token):
    "usage: {% auto_sort queryset %}"
    try:
        tag_name, queryset = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
    return SortedQuerysetNode(queryset)
    
class SortedQuerysetNode(template.Node):
    def __init__(self, queryset):
        self.queryset_var = queryset
        self.queryset = template.Variable(queryset)
        
    def render(self, context):
        queryset = self.queryset.resolve(context)
        if 'request' in context:
            request = context['request']
            sort_by = request.GET.get('sort_by')
            has_visible_name = False
            if sort_by:
                if sort_by in [el.name for el in queryset.model._meta.fields]:
                    queryset = queryset.order_by(sort_by)
                else:
                    has_visible_name = True
                    if sort_by in request.session:
                        sort_by = request.session[sort_by]
                        try:
                            queryset = queryset.order_by(sort_by)
                        except:
                            raise
        context[self.queryset_var] = queryset
        if 'request' in context:
            getvars = request.GET.copy()
        else:
            getvars = {}
        if 'sort_by' in getvars:
            if has_visible_name:
                context['current_sort_field']= request.session.get(getvars['sort_by']) or getvars['sort_by'] 
            else:
                context['current_sort_field']= getvars['sort_by']
            del getvars['sort_by']
        if len(getvars.keys()) > 0:
            context['getsortvars'] = "&%s" % getvars.urlencode()
        else:
            context['getsortvars'] = ''
        return ''
