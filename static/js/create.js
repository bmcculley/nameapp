var contentType ="application/x-www-form-urlencoded; charset=utf-8";
$(function() {
  $("input[name=firstname]").select();
  $(":input").inputmask();
  
  // show the create person form
  $("#show-add").on("click", function() {
    console.log( "Showing the create person form" );
    $(this).addClass("hidden");                 
    $("#cpform").removeClass("hidden").addClass("bounce animated");
    $("input[name=firstname]").select();
  });
  
  $(".cl-cpform").on("click", function() {
    console.log( "Hiding the create person form" );                 
    $("#cpform").addClass("fadeOutUp animated").delay(800).queue(function(){
        $(this).removeClass("fadeOutUp").addClass("hidden").dequeue();
        $("#show-add").removeClass("hidden");
    });
  });

  function isValidDate(dateString) {
    var regEx = /^\d{4}-\d{2}-\d{2}$/;
    return dateString.match(regEx) != null;
  }

  // submit the create person form
  $("form.compose").submit(function(e) {
    e.preventDefault();
    var required = ["firstname", "lastname", "dob", "zip_code"];
    var form = $(this).get(0);
    for (var i = 0; i < required.length; i++) {
      if (!form[required[i]].value) {
        $(form[required[i]]).select();
        if (required[i] == "firstname") {
          var astr = "First name";
        } else if (required[i] == "lastname") {
          var astr = "Last name";
        } else if (required[i] == "dob") {
          var astr = "Date of birth";
        } else if (required[i] == "zip_code") {
          var astr = "Zip code";
        } else {
          var astr = "Unknown parameter";
        }
        customAlert("Error:", astr+" required.", "danger");
        return false;
      }
    }

    if ( !isValidDate( $('#dob').val() ) ) {
      console.log("Date of birth is invalid.");
      customAlert("Error:", "Date of birth is in an invalid format.", "danger");
      return false;
    }

    console.log("posting ajax");
    $.ajax({
      type : "POST",
      url : "http://demo.mkdir.info/create",
        dataType : "json",
        data: {
          firstname: $("#firstname").val(),
          lastname: $("#lastname").val(),
          dob: $("#dob").val(),
          zip_code: $("#zip_code").val(),
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
            console.log(data);
            customAlert("Success:", data.message, "success");
            $( ".persons-table" ).prepend("<tr><td>"+$("#firstname").val()+"</td><td>"+$("#lastname").val()+"</td><td>"+$("#dob").val()+"</td><td>"+$("#zip_code").val()+"</td><td><a href=\"/create?id="+data.in_id+"\" data-toggle=\"modal\" data-target=\"#updateModal\">Edit</a>&nbsp;&nbsp;<a href=\"/create?id="+data.in_id+"&d=t\" title=\"Delete\" class=\"d-link text-danger\"><i class=\"glyphicon glyphicon-trash\"></i></a></td></tr>");
            $("#firstname").val("");
            $("#lastname").val("");
            $("#dob").val("");
            $("#zip_code").val("");
            $("input[name=firstname]").select();
          }
        },
        error : function(XMLHttpRequest, textStatus, errorThrown) {
          // something went terribly wrong
          customAlert("Error:", "something went terribly wrong", "danger");
        }
      });
    return false;
  });

  // update a person
  $(".e-link").on("click", function() {
    console.log( "Updating: " + $(this).data("pid") );
    $("#updateModal [name=\"id\"]").val( $(this).data("pid") );
    var count = 0;
    $(this).closest("tr").find("td").each (function() {
      if ( count === 0 ) {
        console.log( "First name: " + $(this).text() );
        $("#updateModal #firstname").val( $(this).text() );
      } else if ( count === 1 ) {
        console.log( "Last name: " + $(this).text() );
        $("#updateModal #lastname").val( $(this).text() );
      } else if ( count === 2 ) {
        console.log( "DOB: " + $(this).text() );
        $("#updateModal #dob").val( $(this).text() );
      } else if ( count === 3 ) {
        console.log( "Zipcode: " + $(this).text() );
        $("#updateModal #zip_code").val( $(this).text() );
      }
      count++;
    });
  });
});
