let timerInterval;

function updateContent() {
    $('#timer').text("Обновление...");

    $.ajax({
        url: window.location.pathname + 'update_partial/',
        type: 'GET',
        success: function(data) {
            $('#monitors').html(data);
            console.log('Updated content loaded');
            resetTimer();
            failCheck();
        },
        error: function(xhr, status, error) {
            console.error('Error fetching updated content:', error);
        }
    });
}

function updateTimer() {
    let seconds = 60;
    timerInterval = setInterval(function() {
        seconds--;
        let remainingSeconds = seconds % 60;

        function getDeclension(number, titles) {
            let cases = [2, 0, 1, 1, 1, 2];
            return titles[(number % 100 > 4 && number % 100 < 20) ? 2 : cases[(number % 10 < 5) ? number % 10 : 5]];
        }

        let text = "Следующее обновление через " + remainingSeconds + " " + getDeclension(remainingSeconds, ['секунду', 'секунды', 'секунд']) + ".";
        $('#timer').text(text);

        if (seconds <= 0) {
            clearInterval(timerInterval);
        }
    }, 1000);
}

function resetTimer() {
    clearInterval(timerInterval);
    updateTimer();
}

function failCheck() {
    let anyDown = false;
    $('.status').each(function() {
        if ($(this).text() === "Состояние: Недоступен") {
            anyDown = true;
            return false;
        }
    });

    if (anyDown) {
        $('.hero').removeClass('is-primary').addClass('has-background-danger-dark');
    } else {
        $('.hero').removeClass('has-background-danger-dark').addClass('is-primary');
    }

    return anyDown;
}

setInterval(updateContent, 60000);
updateTimer();
failCheck();