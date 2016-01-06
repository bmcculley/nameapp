var contentType ="application/x-www-form-urlencoded; charset=utf-8";
$(function() {
  $("input[name=email]").select();
  $("form.cu-form").submit(function(e) {
    e.preventDefault();
    var required = ["email", "password"];
    var form = $(this).get(0);
    for (var i = 0; i < required.length; i++) {
      if (!form[required[i]].value) {
        $(form[required[i]]).select();
        if (required[i] == "email") {
          var astr = "Email or Username";
        } else if (required[i] == "password") {
          var astr = "Password";
        } else {
          var astr = "Unknown parameter";
        }
        customAlert("Error:", astr+" required.", "danger");
        return false;
      }
    }
    console.log("posting ajax");
    $.ajax({
      type : "POST",
      url : "/auth/login",
        dataType : "json",
        data: {
          email: $("#email").val(),
          password: $("#password").val(),
          _xsrf: $("[name=_xsrf]").val()
        },
        contentType: contentType,
        success : function(data){
          if (data.error === "true") {
            // there was an error
            customAlert("Error:", data.message, "danger");
          }
          else if (data.error === "false") {
            // okay
            console.log(data.cookie_data);
            customAlert("Success:", data.message, "success");
            window.location.href = "/";
          }
        },
        error : function(XMLHttpRequest, textStatus, errorThrown) {
          // something went terribly wrong
          customAlert("Error:", "something went terribly wrong", "danger");
        }
      });
    return false;
  });
});