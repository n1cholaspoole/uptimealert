const interval_value = document.querySelector("#interval_value");
const interval_input = document.querySelector("#interval");

const threshold_value = document.querySelector("#threshold_value");
const threshold_input = document.querySelector("#threshold");

function getDeclension(number, titles) {
    let cases = [2, 0, 1, 1, 1, 2];
    return titles[(number % 100 > 4 && number % 100 < 20) ? 2 : cases[(number % 10 < 5) ? number % 10 : 5]];
}

interval_input.addEventListener("input", (event) => {
  interval_value.textContent = `${event.target.value} ${getDeclension(event.target.value, ["минута","минуты","минут"])}.`;
});

threshold_input.addEventListener("input", (event) => {
  threshold_value.textContent = `${event.target.value} ${getDeclension(event.target.value, ["раз","раза","раз"])}.`;
});
