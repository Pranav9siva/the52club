from .models import Collaborator

def global_context(request):
    """
    Context processor to make active Collaborators available in all templates
    (e.g., for rendering the extended footer).
    """
    collaborators = Collaborator.objects.filter(is_active=True)
    
    # Group collaborators by category
    categories = {}
    for item in collaborators:
        cat = item.category.strip().upper()
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)

    return {
        'footer_collaborators': collaborators,
        'footer_collaborations_grouped': categories,
    }
