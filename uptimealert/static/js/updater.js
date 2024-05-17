let timerInterval;

function updateContent() {
    $('#timer').text("Updating...");

    $.ajax({
        url: window.location.pathname + 'update_partial/',
        type: 'GET',
        success: function(data) {
            $('#monitors').html(data);
        },
        error: function(xhr, status, error) {
            console.error('Error fetching updated content:', error);
        }
    });
    resetTimer();
    failCheck();
}

function updateTimer() {
    let seconds = 60;
    timerInterval = setInterval(function() {
        seconds--;
        let remainingSeconds = seconds % 60;
        $('#timer').text("Next update in " + remainingSeconds + " seconds.");
    }, 1000);
}

function resetTimer() {
    clearInterval(timerInterval);
    updateTimer();
}

function failCheck() {
    let anyDown = false;
    $('.status').each(function() {
        if ($(this)[0].innerText === "Status: Down") {
            anyDown = true;
            return false;
        }
    });

    if (anyDown) {
        $('.hero').removeClass('is-primary').addClass('has-background-danger-dark');
    } else {
        $('.hero').removeClass('has-background-danger-dark').addClass('is-primary');
    }

    return anyDown
}

setInterval(updateContent, 60000);
updateTimer();
failCheck();
