from aussieshopper import settings


def export_settings(request):
    """
    Add some useful settings to the templates
    """
    return {
        'USE_GOOGLE_ANALYTICS': settings.USE_GOOGLE_ANALYTICS
    }
