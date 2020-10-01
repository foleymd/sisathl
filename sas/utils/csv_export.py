import csv
from django.http import HttpResponse
from django.utils.text import slugify


def convert_dicts_to_CSV_response(dicts_to_export,
                                  field_keys,
                                  csv_title="download",
                                  header_msg=None,
                                  field_display_titles=None):
    """Returns a CSV response given a dictionary.
    Required:
    dicts_to_export = list of dicts; each dict should represent one row
    field_keys = an ordered list representing the dict keys
    Optional:
    header_msg = A list of items representing extra rows that print
                 at the top of the file. One list item = one row.
    field_display_titles = The column headers as an ordered list
    csv_title = the name of the exported file
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; ' \
                                      'filename="%s.csv"' % slugify(unicode(csv_title))
    writer = csv.writer(response)
    if header_msg:
        for row in header_msg:
            writer.writerow([row])
    if field_display_titles:
        writer.writerow(field_display_titles)
    for item in dicts_to_export:
        row = [item.get(key, '') for key in field_keys]
        writer.writerow(row)
    return response


class CSVFromDictsResponseMixin(object):
    """
    A generic mixin that constructs a CSV response from the context data if
    the CSV export option was provided in the request. It expects the context
    data to be in the form of a dict.
    Required view attributes:
    context_object_name = should refer to a list of dicts in the context
    field_keys = an ordered list representing the dict keys
    csv_title = the name of the exported file
    Optional:
    header_msg = A list of items representing extra rows that print
                 at the top of the file. One list item = one row.
    field_display_titles = The column headers as an ordered list
    """
    def render_to_response(self, context, **response_kwargs):
        """
        Creates a CSV response if requested, otherwise returns the default
        template response.
        """
        if 'csv' in self.request.GET.get('export', ''):
            dicts_to_export = context[self.context_object_name]
            try:
                header_msg = self.header_msg
            except AttributeError:
                header_msg = None
            try:
                field_display_titles = self.field_display_titles
            except AttributeError:
                field_display_titles = None
            response = convert_dicts_to_CSV_response(dicts_to_export,
                                                     self.field_keys,
                                                     self.csv_title,
                                                     header_msg=header_msg,
                                                     field_display_titles=field_display_titles)
            return response
        else:
            return super(CSVFromDictsResponseMixin, self).render_to_response(
                context, **response_kwargs)



