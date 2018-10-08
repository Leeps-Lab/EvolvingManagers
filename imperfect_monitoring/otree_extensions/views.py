import datetime
import vanilla


class ExportCSV(vanilla.View):

    url_name = 'imperfect_monitoring_custom_export'
    url_pattern = '^{}/$'.format(url_name)
    display_name = 'Imperfect Monitoring Custom Export'

    def get(request, *args, **kwargs):

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            '{} Events (accessed {}).csv'.format(
                ExportCSV.display_name,
                datetime.date.today().isoformat()
            )
        )

        w = csv.writer(response)
        # TODO: w.writerows([...])
        return response
