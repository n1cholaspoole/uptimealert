const interval_value = document.querySelector("#interval_value");
const interval_input = document.querySelector("#interval");

const threshold_value = document.querySelector("#threshold_value");
const threshold_input = document.querySelector("#threshold");

interval_value.textContent = interval_input.value;
threshold_value.textContent = threshold_input.value;

interval_input.addEventListener("input", (event) => {
  interval_value.textContent = event.target.value;
});

threshold_input.addEventListener("input", (event) => {
  threshold_value.textContent = event.target.value;
});
