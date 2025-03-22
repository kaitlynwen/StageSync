window.onload = function() {
    {% if success_message %}
        alert("{{ success_message }}");
    {% endif %}
}