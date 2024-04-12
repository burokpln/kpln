const fieldWrappers = document.querySelectorAll(
  ".tep_info_form__field_wrapper"
);

fieldWrappers.forEach((wrapper) => {
  const label = wrapper.querySelector("label");

  if (label.textContent.includes("%")) {
    wrapper.id = "percentage_column";
  }
});
