$('form').on('submit', function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    $.ajax({
        url: '/game/create',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function (response) {
            console.log('Что-то пошло не так');
            if (response.success && response.game_url) {
                window.location.href = response.game_url;
            } else {
                alert(response.message || 'Что-то пошло не так');
            }
        },
        error: function (xhr) {
            console.log('error');

            try {
                const res = JSON.parse(xhr.responseText);
                alert('Ошибка: ' + (res.message || 'Неизвестная ошибка'));
            } catch {
                alert('Ошибка сервера');
            }
        }
    });
});
