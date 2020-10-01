$(document).ready(function(){

    // The function toggleFields checks each 'countable' field to see
    // if it is set to ' ', 'N', or 'Y'. If it is set to 'Y', it shows
    // the other fields in that row. If it is set to ' ' or 'N', it hides them (and resets their value).
    // It works under the assumption that the fields have an id with format id_<prefix>-<number>-<field_name>
    function toggleFields(){
        $(".countable").each(function() {

            // Use regex to get the id number for that row. Match returns an array of values, so
            // use [0] to look just at the first item it returns.
            id_number = $(this).attr('id').match(/[\d]{1,2}/)[0];

            // get the type, 'cou' or 'adl'
            type = $(this).attr('id').substring(3,6);

            id_prefix = "#id_" + type + "-" + id_number;

            // toggle fields with same id and type
            if ($(this).val() !== "Y") {
                  $(id_prefix + "-min_grade_required").hide();
                  $(id_prefix + "-pass_fail_accepted").hide();
                  $(id_prefix + "-min_grade_required").val(""); 
                  $(id_prefix + "-pass_fail_accepted").val("");
            } else {
                  $(id_prefix + "-min_grade_required").show();
                  $(id_prefix + "-pass_fail_accepted").show();  
            }
       });
    } // end toggleFields
    
    // on load and on each change we toggle the fields
    toggleFields(); 
    $(".countable").change(function () {
        toggleFields(); 
    });


}); // end document.ready
