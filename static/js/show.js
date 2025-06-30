$(document).ready(function () {
    $("#show-nav, #nav-bg").click(function () {
        $("#show-nav").toggleClass("active");
        $("#nav-bg").toggleClass("active");
        $("#nav").toggleClass("visible");
        $('body').toggleClass('no-scroll');
    });
});


const modal = $('#gameModal');

if (modal.data('linked-app')) {
    modal.css('display', 'flex');
}

$(window).on('click', function (e) {
    if (e.target.id === 'gameModal') closeModal();
});

$(window).on('keydown', function (e) {
    if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        closeModal();
    }
});

function closeModal() {
    $('#gameModal').hide();
    document.body.classList.remove('no-scroll');

    if (modal.data('linked-app')) {
        window.location.href = 'https://appw.su/';
    } else {
        history.pushState(null, '', '/');
    }
}
