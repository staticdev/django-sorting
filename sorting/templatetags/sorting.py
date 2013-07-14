from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from sorting.util import label_for_field
from sorting.views import ORDER_VAR

register = template.Library()


def result_headers(cl):
    """
    Generates the list column headers.
    """
    ordering_field_columns = cl.get_ordering_field_columns()
    for i, field_name in enumerate(cl.list_display):
        text, attr = label_for_field(field_name, cl.model, return_attr=True)
        if attr:
            # Potentially not sortable

            # if the field is the action checkbox: no sorting and special class
            if field_name == 'action_checkbox':
                yield {
                    "text": text,
                    "class_attrib": mark_safe(' class="action-checkbox-column"'),
                    "sortable": False,
                }
                continue

#            if outros_fields:
                # Not sortable
#                yield {
#                    "text": text,
#                    "class_attrib": format_html(' class="column-{0}"', field_name),
#                    "sortable": False,
#                }
#                continue

        # OK, it is sortable if we got this far
        th_classes = ['sortable', 'column-{0}'.format(field_name)]
        order_type = ''
        new_order_type = 'asc'
        sorted = False
        # Is it currently being sorted on?
        if i in ordering_field_columns:
            sorted = True
            order_type = ordering_field_columns.get(i).lower()
            th_classes.append('sorted %sending' % order_type)
            new_order_type = {'asc': 'desc', 'desc': 'asc'}[order_type]

        # build new ordering param
        o_list_primary = []  # URL for making this field the primary sort
        o_list_toggle = []  # URL for toggling order type for this field
        make_qs_param = lambda t, n: ('-' if t == 'desc' else '') + str(n)

        for j, ot in ordering_field_columns.items():
            if j == i:  # Same column
                param = make_qs_param(new_order_type, j)
                # We want clicking on this header to bring the ordering to the
                # front
                o_list_primary.insert(0, param)
            else:
                param = make_qs_param(ot, j)
                o_list_primary.append(param)
                o_list_toggle.append(param)

        if i not in ordering_field_columns:
            o_list_primary.insert(0, make_qs_param(new_order_type, i))

        yield {
            "text": text,
            "sortable": True,
            "sorted": sorted,
            "ascending": order_type == "asc",
            "url_primary": cl.get_query_string({ORDER_VAR: '.'.join(o_list_primary)}),
            "url_toggle": cl.get_query_string({ORDER_VAR: '.'.join(o_list_toggle)}),
            "class_attrib": format_html(' class="{0}"', ' '.join(th_classes)) if th_classes else '',
        }


@register.inclusion_tag('sorting/change_list_headers.html')
def result_headers(cl):
    """
    Displays the headers and data list together
    """
    headers = list(result_headers(cl))
    sorted_fields = False
    for h in headers:
        if h['sortable'] and h['sorted']:
            sorted_fields = True
    return {'cl': cl,
            'result_headers': headers,
            'sorted_fields': sorted_fields}

# TO-DO: receive a list and make a for in the template
@register.inclusion_tag('sorting/sort_link_frag.html', takes_context=True)
def sort_link(context, text, sort_field, visible_name=None):
    """Usage: {% sort_link "text" "field_name" %}
    Usage: {% sort_link "text" "field_name" "Visible name" %}
    """
    sorted_fields = False
    ascending = None
    class_attrib = 'sortable'
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
