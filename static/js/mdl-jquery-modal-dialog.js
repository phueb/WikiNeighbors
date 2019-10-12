function showLoading() {
    // remove existing loaders
    $('.loading-container').remove();
    $('<div id="loader-div" class="loading-container"><div><div class="mdl-spinner mdl-js-spinner is-active"></div></div></div>').appendTo("body");

    componentHandler.upgradeElements($('.mdl-spinner').get());
    setTimeout(function () {
        $('#loader-div').css({opacity: 1});
    }, 1);
}

