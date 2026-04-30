from django.shortcuts import render, redirect
from django.contrib import messages


def landing_view(request):
    """Landing page - frontend only."""
    return render(request, 'core/landing.html', {})


def login_view(request):
    """Login page - frontend only, no backend logic."""
    return render(request, 'core/login.html', {})


def logout_view(request):
    """Logout - redirect to login page."""
    return redirect('/login/')


def register_view(request):
    """Registration page - frontend only, no backend logic."""
    return render(request, 'core/register.html', {})


def dashboard_admin(request):
    """Admin dashboard - frontend only."""
    return render(request, 'core/dashboard_admin.html', {})


def dashboard_organizer(request):
    """Organizer dashboard - frontend only."""
    return render(request, 'core/dashboard_organizer.html', {})


def dashboard_customer(request):
    """Customer dashboard - frontend only."""
    return render(request, 'core/dashboard_customer.html', {})


def profile_customer(request):
    """Customer profile page - frontend only."""
    return render(request, 'core/profile_customer.html', {})


def profile_organizer(request):
    """Organizer profile page - frontend only."""
    return render(request, 'core/profile_organizer.html', {})


def profile_admin(request):
    """Admin profile page - frontend only."""
    return render(request, 'core/profile_admin.html', {})

artists = [
    {
        "id": "ART001",
        "name": "Fourtwnty",
        "genre": "Indie Folk",
        "on_event": True
    },
    {
        "id": "ART002",
        "name": "Hindia",
        "genre": "Indie Pop",
        "on_event": True
    },
    {
        "id": "ART003",
        "name": "Tulus",
        "genre": "Pop",
        "on_event": True
    },
    {
        "id": "ART004",
        "name": "Nadin Amizah",
        "genre": "Folk",
        "on_event": True
    },
    {
        "id": "ART005",
        "name": "Pamungkas",
        "genre": "Singer-Songwriter",
        "on_event": True
    },
    {
        "id": "ART006",
        "name": "Raisa",
        "genre": "R&B / Pop",
        "on_event": True
    },
]


def artist_list(request):
    search_query = request.GET.get("search", "").lower()

    filtered_artists = artists

    if search_query:
        filtered_artists = [
            artist for artist in artists
            if search_query in artist["name"].lower()
            or search_query in artist["genre"].lower()
        ]

    sorted_artists = sorted(filtered_artists, key=lambda x: x["name"])

    total_artists = len(artists)

    total_genres = len(set(
        artist["genre"] for artist in artists
    ))

    total_event_artists = len([
        artist for artist in artists
        if artist["on_event"]
    ])

    context = {
        "artists": sorted_artists,
        "total_artists": total_artists,
        "total_genres": total_genres,
        "total_event_artists": total_event_artists,
        "search_query": search_query,
        "artist_found": len(sorted_artists),
        "role": "admin"
    }

    return render(request, "artist/artist_list.html", context)

def artist_create(request):
    context = {
        'role': 'admin',
    }

    if request.method == "POST":
        name = request.POST.get("name")
        genre = request.POST.get("genre")

        if not name:
            messages.error(request, "Name wajib diisi.")
            return render(request, "artist/artist_create.html")

        messages.success(request, "Artist berhasil ditambahkan.")
        return redirect("artist_list")

    return render(request, "artist/artist_create.html", context)


def artist_update(request, id):
    artist = next((a for a in artists if a["id"] == id), None)
    
    context = {
        'role': 'admin',
        'artist': artist
    }

    if request.method == "POST":
        name = request.POST.get("name")
        genre = request.POST.get("genre")

        if not name:
            messages.error(request, "Name wajib diisi.")
            return render(request, "artist/artist_update.html", context)

        messages.success(request, "Artist berhasil diperbarui.")
        return redirect("artist_list")

    return render(request, "artist/artist_update.html", context)


def artist_delete(request, id):
    artist = next((a for a in artists if a["id"] == id), None)

    context = {
        'role': 'admin',
        'artist': artist
    }

    if request.method == "POST":
        messages.success(request, "Artist berhasil dihapus.")
        return redirect("artist_list")

    return render(request, "artist/artist_delete.html", context)


ticket_categories = [
{
"id": "CAT001",
"name": "VIP",
"quota": 100,
"price": 500000,
"event": "Coldplay Concert"
},
{
"id": "CAT002",
"name": "Regular",
"quota": 300,
"price": 200000,
"event": "Coldplay Concert"
}
]
def artist_read(request):
    """Fitur 10 - R Artist (customer/organizer/admin, tanpa action button)"""
    return render(request, 'artist/artist_read.html')

def ticket_category_list(request):
    """
    Fitur 11/12 - CUD + R Ticket Category
    Tampilan ini: sidebar admin, dengan tombol tambah + modal CUD
    URL: /ticket-categories/
    """
    return render(request, 'ticket_category/ticket_category_list.html')

def ticket_category_list_customer(request):
    """
    Fitur 12 - R Ticket Category
    Tampilan untuk Customer/Guest - read only, tanpa tombol aksi
    URL: /ticket-categories/customer/
    """
    return render(request, 'ticket_category/ticket_category_list_customer.html')