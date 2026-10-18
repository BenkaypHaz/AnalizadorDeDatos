from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .forms import NumeroForm, TextoForm


@require_http_methods(["GET", "POST"])
def inicio(request):
    form_numero = NumeroForm(prefix="num")
    form_texto = TextoForm(prefix="txt")
    contexto = {}

    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "numero":
            form_numero = NumeroForm(request.POST, prefix="num")
            if form_numero.is_valid():
                contexto["resultado"] = form_numero.cleaned_data["resultado"]
        elif accion == "texto":
            form_texto = TextoForm(request.POST, prefix="txt")
            if form_texto.is_valid():
                analisis = form_texto.cleaned_data["analisis"]
                contexto["analisis"] = analisis
                contexto["total_bytes"] = sum(c.cantidad_bytes for c in analisis)
        contexto["accion"] = accion

    contexto.update(form_numero=form_numero, form_texto=form_texto)
    return render(request, "conversor/inicio.html", contexto)
