$('form').on('submit', function (e) {
    e.preventDefault();
    var formData = new FormData(this);
    $.ajax({
        url: '/game/create',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
            alert(response.message);
            if (response.success) {
                window.location.href = response.game_url;
            }
        },
        error: function (xhr) {
            var res = JSON.parse(xhr.responseText);
            alert('Ошибка: ' + res.message);
        }
    });
});