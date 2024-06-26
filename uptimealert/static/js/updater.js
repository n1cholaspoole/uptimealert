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
    let seconds = 10;
    timerInterval = setInterval(function() {
        seconds--;
        let remainingSeconds = seconds % 60;

        if (seconds <= 0) {
            clearInterval(timerInterval);
            return;
        }
        
        function getDeclension(number, titles) {
            let cases = [2, 0, 1, 1, 1, 2];
            return titles[(number % 100 > 4 && number % 100 < 20) ? 2 : cases[(number % 10 < 5) ? number % 10 : 5]];
        }

        let text = `Следующее обновление через ${remainingSeconds} ${getDeclension(remainingSeconds, ['секунду', 'секунды', 'секунд'])}.`;
        $('#timer').text(text);

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
            $(this).parent().addClass('has-background-danger').addClass('round');
            $(this).addClass('has-text-black');
        } else {
            $(this).parent().removeClass('has-background-danger').removeClass('round');
        }
    });

    if (anyDown) {
        $('.hero').removeClass('is-primary').addClass('has-background-danger-dark');
    } else {
        $('.hero').removeClass('has-background-danger-dark').addClass('is-primary');
    }

    return anyDown;
}

setInterval(updateContent, 10000);
updateTimer();
failCheck();