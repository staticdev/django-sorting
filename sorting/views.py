from django.utils.datastructures import SortedDict
from django.utils.http import urlencode

ORDER_VAR = 'o'


class SimpleChangeList():
    def __init__(self, request, model, list_display, list_display_links,
                 list_filter, search_fields, list_select_related,
                 list_per_page, list_max_show_all, list_editable):
        self.model = model
        self.list_display = list_display
        self.list_display_links = list_display_links
        self.list_filter = list_filter

        self.list_select_related = list_select_related
        self.list_per_page = list_per_page
        self.list_max_show_all = list_max_show_all

    def get_ordering_field_columns(self):
        """
        Returns a SortedDict of ordering field column numbers and asc/desc
        """

        # We must cope with more than one column having the same underlying sort
        # field, so we base things on column numbers.
        ordering = self._get_default_ordering()
        ordering_fields = SortedDict()
        if ORDER_VAR not in self.params:
            # for ordering specified on model Meta, we don't know
            # the right column numbers absolutely, because there might be more
            # than one column associated with that ordering, so we guess.
            for field in ordering:
                if field.startswith('-'):
                    field = field[1:]
                    order_type = 'desc'
                else:
                    order_type = 'asc'
                for index, attr in enumerate(self.list_display):
                    if self.get_ordering_field(attr) == field:
                        ordering_fields[index] = order_type
                        break
        else:
            for p in self.params[ORDER_VAR].split('.'):
                none, pfx, idx = p.rpartition('-')
                try:
                    idx = int(idx)
                except ValueError:
                    continue  # skip it
                ordering_fields[idx] = 'desc' if pfx == '-' else 'asc'
        return ordering_fields

    def get_query_string(self, new_params=None, remove=None):
        if new_params is None:
            new_params = {}
        if remove is None:
            remove = []
        p = self.params.copy()
        for r in remove:
            for k in list(p):
                if k.startswith(r):
                    del p[k]
        for k, v in new_params.items():
            if v is None:
                if k in p:
                    del p[k]
            else:
                p[k] = v
        return '?%s' % urlencode(sorted(p.items()))
