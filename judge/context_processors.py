from .models import IndexString

# Custom context processors
def index_string(request):
    return {'index_string': IndexString.objects.get(pk=1).index_str}

def index_string_plural(request):
    return {'index_string_plural': IndexString.objects.get(pk=1).index_str_plural}
