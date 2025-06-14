$(document).ready(function() {
    $("#show-nav, #nav-bg").click(function() {
        $("#show-nav").toggleClass("active");
        $("#nav-bg").toggleClass("active");
        $("#nav").toggleClass("visible");
    });
});